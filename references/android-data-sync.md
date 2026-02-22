# Android Data Synchronization & Offline-First

Modern data synchronization patterns for offline-first Android apps with conflict resolution, cache invalidation, network monitoring, and retry strategies.

All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

**Related guides:** 
- See `references/architecture.md` for repository patterns and data layer architecture
- See `references/coroutines-patterns.md` for async operations and structured concurrency
- See `references/android-notifications.md` for WorkManager and foreground service sync

## Table of Contents

- [Offline-First Architecture](#offline-first-architecture)
- [Network State Monitoring](#network-state-monitoring)
- [Sync Strategies](#sync-strategies)
- [Conflict Resolution](#conflict-resolution)
- [Cache Invalidation](#cache-invalidation)
- [Retry Mechanisms](#retry-mechanisms)
- [WorkManager Integration](#workmanager-integration)
  - [Work Constraints](#work-constraints)
  - [Work Chaining](#work-chaining)
  - [Passing Data Between Workers](#passing-data-between-workers)
  - [Progress Updates](#progress-updates)
  - [Testing WorkManager](#testing-workmanager)
- [Repository Pattern for Sync](#repository-pattern-for-sync)
- [Architecture Integration](#architecture-integration)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Offline-First Architecture

Local database is the **single source of truth**. UI always reads from local database, never directly from network.

### Core Principles

1. **Local database is source of truth** - Room database holds all data
2. **UI observes local data** - ViewModels collect Flow from Repository
3. **Background sync** - WorkManager syncs with remote when connected
4. **Optimistic updates** - Write to local first, sync to remote later
5. **Conflict resolution** - Handle server rejections and merge conflicts

### Architecture Flow

```
┌──────────────┐
│   UI Layer   │
└──────┬───────┘
       │ observes Flow
       │
┌──────▼────────────────────────────────────┐
│          Repository                       │
│  ┌────────────────────────────────────┐   │
│  │  Local DB (Room) - Source of Truth│   │
│  └────────────────────────────────────┘   │
│               ▲         │                 │
│               │         │                 │
│     ┌─────────┴─────────▼───────┐         │
│     │   Sync Coordinator        │         │
│     │   (WorkManager)           │         │
│     └─────────┬─────────▲───────┘         │
│               │         │                 │
│  ┌────────────▼─────────┴──────────────┐  │
│  │      Remote API                     │  │
│  └─────────────────────────────────────┘  │
└───────────────────────────────────────────┘
```

### Repository with Offline-First

```kotlin
// core/data/TaskRepository.kt
@Singleton
class TaskRepositoryImpl @Inject constructor(
    private val taskDao: TaskDao,
    private val taskApi: TaskApi,
    private val networkMonitor: NetworkMonitor,
    private val syncCoordinator: SyncCoordinator
) : TaskRepository {

    // UI observes this - always from local DB
    override fun observeTasks(): Flow<List<Task>> = taskDao.observeAll()
        .map { entities -> entities.map { it.toDomain() } }

    override fun observeTask(id: String): Flow<Task?> = taskDao.observeById(id)
        .map { it?.toDomain() }

    // Write to local first (optimistic update)
    override suspend fun createTask(task: Task): Result<Task> = runCatching {
        val entity = task.toEntity().copy(
            syncStatus = SyncStatus.PENDING_CREATE,
            lastModified = Clock.System.now()
        )
        taskDao.insert(entity)
        
        // Schedule background sync
        syncCoordinator.scheduleSyncNow()
        
        task
    }

    override suspend fun updateTask(task: Task): Result<Task> = runCatching {
        val entity = task.toEntity().copy(
            syncStatus = SyncStatus.PENDING_UPDATE,
            lastModified = Clock.System.now()
        )
        taskDao.update(entity)
        
        syncCoordinator.scheduleSyncNow()
        
        task
    }

    override suspend fun deleteTask(id: String): Result<Unit> = runCatching {
        taskDao.markAsDeleted(id, Clock.System.now())
        syncCoordinator.scheduleSyncNow()
    }

    // Background sync - called by WorkManager
    override suspend fun syncPendingChanges(): SyncResult {
        if (!networkMonitor.isConnected()) {
            return SyncResult.NoNetwork
        }

        val pendingTasks = taskDao.getPendingSync()
        val results = mutableListOf<SyncItemResult>()

        for (task in pendingTasks) {
            val result = when (task.syncStatus) {
                SyncStatus.PENDING_CREATE -> syncCreate(task)
                SyncStatus.PENDING_UPDATE -> syncUpdate(task)
                SyncStatus.PENDING_DELETE -> syncDelete(task)
                else -> continue
            }
            results.add(result)
        }

        return if (results.all { it is SyncItemResult.Success }) {
            SyncResult.Success(results.size)
        } else {
            val failures = results.filterIsInstance<SyncItemResult.Failed>()
            SyncResult.PartialSuccess(
                successCount = results.size - failures.size,
                failures = failures
            )
        }
    }

    private suspend fun syncCreate(task: TaskEntity): SyncItemResult = try {
        val response = taskApi.createTask(task.toApiModel())
        taskDao.update(
            task.copy(
                serverId = response.id,
                syncStatus = SyncStatus.SYNCED,
                serverVersion = response.version
            )
        )
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun syncUpdate(task: TaskEntity): SyncItemResult = try {
        val response = taskApi.updateTask(task.serverId!!, task.toApiModel())
        
        if (response.version <= task.serverVersion) {
            // Server has newer version - conflict!
            return resolveConflict(task, response)
        }
        
        taskDao.update(
            task.copy(
                syncStatus = SyncStatus.SYNCED,
                serverVersion = response.version
            )
        )
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun syncDelete(task: TaskEntity): SyncItemResult = try {
        taskApi.deleteTask(task.serverId!!)
        taskDao.delete(task.id)
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun handleSyncError(
        task: TaskEntity,
        error: Exception
    ): SyncItemResult {
        return when {
            error is HttpException && error.code() == 409 -> {
                SyncItemResult.Conflict(task.id, error.message())
            }
            error is HttpException && error.code() in 400..499 -> {
                // Client error - mark as failed, don't retry
                taskDao.update(task.copy(syncStatus = SyncStatus.FAILED))
                SyncItemResult.Failed(task.id, error.message())
            }
            else -> {
                // Transient error - will retry later
                SyncItemResult.Retry(task.id, error.message ?: "Unknown error")
            }
        }
    }

    private suspend fun resolveConflict(
        localTask: TaskEntity,
        remoteTask: ApiTask
    ): SyncItemResult {
        // Server wins strategy (can be customized per app)
        taskDao.update(
            localTask.copy(
                title = remoteTask.title,
                description = remoteTask.description,
                status = remoteTask.status,
                serverVersion = remoteTask.version,
                syncStatus = SyncStatus.SYNCED
            )
        )
        return SyncItemResult.ConflictResolved(localTask.id, "Server version applied")
    }
}

enum class SyncStatus {
    SYNCED,
    PENDING_CREATE,
    PENDING_UPDATE,
    PENDING_DELETE,
    FAILED
}

sealed interface SyncResult {
    data class Success(val itemsSynced: Int) : SyncResult
    data class PartialSuccess(
        val successCount: Int,
        val failures: List<SyncItemResult.Failed>
    ) : SyncResult
    data object NoNetwork : SyncResult
    data class Error(val message: String) : SyncResult
}

sealed interface SyncItemResult {
    data class Success(val id: String) : SyncItemResult
    data class Failed(val id: String, val reason: String) : SyncItemResult
    data class Conflict(val id: String, val reason: String) : SyncItemResult
    data class ConflictResolved(val id: String, val resolution: String) : SyncItemResult
    data class Retry(val id: String, val reason: String) : SyncItemResult
}
```

### Room Entity with Sync Metadata

```kotlin
// core/data/database/TaskEntity.kt
@Entity(tableName = "tasks")
data class TaskEntity(
    @PrimaryKey
    val id: String,
    
    @ColumnInfo(name = "server_id")
    val serverId: String? = null,
    
    val title: String,
    val description: String?,
    val status: TaskStatus,
    
    @ColumnInfo(name = "sync_status")
    val syncStatus: SyncStatus,
    
    @ColumnInfo(name = "last_modified")
    val lastModified: Instant,
    
    @ColumnInfo(name = "server_version")
    val serverVersion: Int = 0,
    
    @ColumnInfo(name = "is_deleted")
    val isDeleted: Boolean = false
)

@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks WHERE is_deleted = 0 ORDER BY last_modified DESC")
    fun observeAll(): Flow<List<TaskEntity>>

    @Query("SELECT * FROM tasks WHERE id = :id AND is_deleted = 0")
    fun observeById(id: String): Flow<TaskEntity?>

    @Query("SELECT * FROM tasks WHERE sync_status != 'SYNCED' AND is_deleted = 0")
    suspend fun getPendingSync(): List<TaskEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(task: TaskEntity)

    @Update
    suspend fun update(task: TaskEntity)

    @Query("UPDATE tasks SET is_deleted = 1, last_modified = :timestamp WHERE id = :id")
    suspend fun markAsDeleted(id: String, timestamp: Instant)

    @Query("DELETE FROM tasks WHERE id = :id")
    suspend fun delete(id: String)
}
```

## Network State Monitoring

Monitor network connectivity to determine when to sync.

### Network Monitor Interface

```kotlin
// core/data/network/NetworkMonitor.kt
package com.example.core.data.network

import kotlinx.coroutines.flow.Flow

interface NetworkMonitor {
    val isConnected: Flow<Boolean>
    suspend fun isConnected(): Boolean
}
```

### Implementation with ConnectivityManager

```kotlin
// core/data/network/ConnectivityNetworkMonitor.kt
@Singleton
class ConnectivityNetworkMonitor @Inject constructor(
    @ApplicationContext private val context: Context
) : NetworkMonitor {

    private val connectivityManager = context.getSystemService<ConnectivityManager>()

    private val _isConnected = MutableStateFlow(checkConnection())
    override val isConnected: Flow<Boolean> = _isConnected.asStateFlow()

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            _isConnected.value = true
        }

        override fun onLost(network: Network) {
            _isConnected.value = checkConnection()
        }

        override fun onCapabilitiesChanged(
            network: Network,
            capabilities: NetworkCapabilities
        ) {
            val hasInternet = capabilities.hasCapability(
                NetworkCapabilities.NET_CAPABILITY_INTERNET
            )
            val isValidated = capabilities.hasCapability(
                NetworkCapabilities.NET_CAPABILITY_VALIDATED
            )
            _isConnected.value = hasInternet && isValidated
        }
    }

    init {
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .addCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            .build()

        connectivityManager?.registerNetworkCallback(request, networkCallback)
    }

    override suspend fun isConnected(): Boolean {
        return checkConnection()
    }

    private fun checkConnection(): Boolean {
        val network = connectivityManager?.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
               capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
}
```

### Hilt Module

```kotlin
// core/di/NetworkModule.kt
@Module
@InstallIn(SingletonComponent::class)
abstract class NetworkModule {
    @Binds
    abstract fun bindNetworkMonitor(
        impl: ConnectivityNetworkMonitor
    ): NetworkMonitor
}
```

### Manifest Permission

```xml
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

## Sync Strategies

### 1. One-Way Sync (Server → Local)

Pull latest data from server, overwrite local.

```kotlin
override suspend fun syncFromServer(): SyncResult = runCatching {
    val remoteTasks = taskApi.getTasks()
    val entities = remoteTasks.map { apiTask ->
        TaskEntity(
            id = generateLocalId(),
            serverId = apiTask.id,
            title = apiTask.title,
            description = apiTask.description,
            status = apiTask.status,
            syncStatus = SyncStatus.SYNCED,
            lastModified = apiTask.updatedAt,
            serverVersion = apiTask.version
        )
    }
    
    // Clear and replace (or use upsert for incremental)
    taskDao.deleteAll()
    taskDao.insertAll(entities)
    
    SyncResult.Success(entities.size)
}.getOrElse { e ->
    SyncResult.Error(e.message ?: "Sync failed")
}
```

### 2. Two-Way Sync (Bidirectional)

Merge local and remote changes with conflict resolution.

```kotlin
override suspend fun syncBidirectional(): SyncResult = coroutineScope {
    // Step 1: Push local changes to server
    val pushResult = syncPendingChanges()
    
    // Step 2: Pull remote changes
    val pullResult = async { pullRemoteChanges() }
    
    // Step 3: Merge results
    val pull = pullResult.await()
    
    when {
        pushResult is SyncResult.Success && pull is SyncResult.Success -> {
            SyncResult.Success(pushResult.itemsSynced + pull.itemsSynced)
        }
        else -> {
            SyncResult.PartialSuccess(
                successCount = (pushResult as? SyncResult.Success)?.itemsSynced ?: 0,
                failures = emptyList()
            )
        }
    }
}

private suspend fun pullRemoteChanges(): SyncResult = runCatching {
    val lastSyncTime = preferencesDataSource.getLastSyncTime()
    val remoteTasks = taskApi.getTasksSince(lastSyncTime)
    
    remoteTasks.forEach { apiTask ->
        val localTask = taskDao.getByServerId(apiTask.id)
        
        when {
            localTask == null -> {
                // New remote task - insert
                taskDao.insert(apiTask.toEntity())
            }
            localTask.syncStatus == SyncStatus.SYNCED -> {
                // Local is synced - apply remote changes
                taskDao.update(localTask.copy(
                    title = apiTask.title,
                    description = apiTask.description,
                    status = apiTask.status,
                    serverVersion = apiTask.version,
                    lastModified = apiTask.updatedAt
                ))
            }
            else -> {
                // Conflict - local has pending changes
                resolveConflict(localTask, apiTask)
            }
        }
    }
    
    preferencesDataSource.setLastSyncTime(Clock.System.now())
    SyncResult.Success(remoteTasks.size)
}.getOrElse { e ->
    SyncResult.Error(e.message ?: "Pull failed")
}
```

### 3. Periodic Sync

Use WorkManager for periodic background sync.

```kotlin
// core/sync/SyncWorker.kt
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val taskRepository: TaskRepository,
    private val networkMonitor: NetworkMonitor
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        if (!networkMonitor.isConnected()) {
            return Result.retry()
        }

        return when (val syncResult = taskRepository.syncBidirectional()) {
            is SyncResult.Success -> Result.success()
            is SyncResult.PartialSuccess -> {
                if (syncResult.successCount > 0) {
                    Result.success()
                } else {
                    Result.retry()
                }
            }
            is SyncResult.NoNetwork -> Result.retry()
            is SyncResult.Error -> Result.failure()
        }
    }
}
```

### 4. Event-Driven Sync (Real-Time)

Use WebSockets or Server-Sent Events for real-time updates.

```kotlin
// core/data/realtime/TaskRealtimeSync.kt
@Singleton
class TaskRealtimeSync @Inject constructor(
    private val webSocketClient: WebSocketClient,
    private val taskDao: TaskDao
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    fun startListening() {
        scope.launch {
            webSocketClient.events
                .catch { e -> /* Handle connection errors */ }
                .collect { event ->
                    when (event) {
                        is TaskEvent.Created -> handleCreated(event.task)
                        is TaskEvent.Updated -> handleUpdated(event.task)
                        is TaskEvent.Deleted -> handleDeleted(event.taskId)
                    }
                }
        }
    }

    private suspend fun handleCreated(task: ApiTask) {
        val existing = taskDao.getByServerId(task.id)
        if (existing == null) {
            taskDao.insert(task.toEntity())
        }
    }

    private suspend fun handleUpdated(task: ApiTask) {
        val existing = taskDao.getByServerId(task.id) ?: return
        
        // Only apply if server version is newer
        if (task.version > existing.serverVersion) {
            taskDao.update(existing.copy(
                title = task.title,
                description = task.description,
                status = task.status,
                serverVersion = task.version,
                lastModified = task.updatedAt
            ))
        }
    }

    private suspend fun handleDeleted(taskId: String) {
        taskDao.deleteByServerId(taskId)
    }

    fun stopListening() {
        scope.cancel()
    }
}
```

## Conflict Resolution

Handle cases where local and remote data diverge.

### Conflict Resolution Strategies

#### 1. Server Wins (Default)

```kotlin
private suspend fun resolveConflict(
    local: TaskEntity,
    remote: ApiTask
): SyncItemResult {
    // Discard local changes, apply server version
    taskDao.update(local.copy(
        title = remote.title,
        description = remote.description,
        status = remote.status,
        serverVersion = remote.version,
        syncStatus = SyncStatus.SYNCED,
        lastModified = remote.updatedAt
    ))
    
    return SyncItemResult.ConflictResolved(
        local.id,
        "Server version applied"
    )
}
```

#### 2. Client Wins

```kotlin
private suspend fun resolveConflict(
    local: TaskEntity,
    remote: ApiTask
): SyncItemResult {
    // Force push local changes to server
    return try {
        val updated = taskApi.forceUpdateTask(
            remote.id,
            local.toApiModel(),
            expectedVersion = remote.version
        )
        
        taskDao.update(local.copy(
            serverVersion = updated.version,
            syncStatus = SyncStatus.SYNCED
        ))
        
        SyncItemResult.ConflictResolved(
            local.id,
            "Client version applied"
        )
    } catch (e: Exception) {
        SyncItemResult.Conflict(local.id, e.message ?: "Conflict")
    }
}
```

#### 3. Last Write Wins (Timestamp-Based)

```kotlin
private suspend fun resolveConflict(
    local: TaskEntity,
    remote: ApiTask
): SyncItemResult {
    val useLocal = local.lastModified > remote.updatedAt
    
    return if (useLocal) {
        // Push local to server
        try {
            val updated = taskApi.updateTask(remote.id, local.toApiModel())
            taskDao.update(local.copy(
                serverVersion = updated.version,
                syncStatus = SyncStatus.SYNCED
            ))
            SyncItemResult.ConflictResolved(local.id, "Local (newer) applied")
        } catch (e: Exception) {
            SyncItemResult.Conflict(local.id, e.message ?: "Failed to push")
        }
    } else {
        // Apply remote to local
        taskDao.update(local.copy(
            title = remote.title,
            description = remote.description,
            status = remote.status,
            serverVersion = remote.version,
            syncStatus = SyncStatus.SYNCED,
            lastModified = remote.updatedAt
        ))
        SyncItemResult.ConflictResolved(local.id, "Remote (newer) applied")
    }
}
```

#### 4. Manual Resolution (UI-Driven)

```kotlin
private suspend fun resolveConflict(
    local: TaskEntity,
    remote: ApiTask
): SyncItemResult {
    // Store conflict for user to resolve
    conflictDao.insert(
        ConflictEntity(
            id = generateId(),
            entityId = local.id,
            localVersion = local.toJson(),
            remoteVersion = remote.toJson(),
            createdAt = Clock.System.now()
        )
    )
    
    // Mark entity as conflicted
    taskDao.update(local.copy(
        syncStatus = SyncStatus.CONFLICT
    ))
    
    return SyncItemResult.Conflict(
        local.id,
        "Manual resolution required"
    )
}

// UI to resolve conflicts
@Composable
fun ConflictResolutionScreen(
    conflict: Conflict,
    onResolve: (Resolution) -> Unit
) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text("Conflict detected for: ${conflict.entityName}")
        
        Spacer(modifier = Modifier.height(16.dp))
        
        ConflictVersionCard(
            title = "Your changes",
            data = conflict.localVersion
        )
        
        ConflictVersionCard(
            title = "Server version",
            data = conflict.remoteVersion
        )
        
        Row(modifier = Modifier.fillMaxWidth()) {
            Button(
                onClick = { onResolve(Resolution.UseLocal) },
                modifier = Modifier.weight(1f)
            ) {
                Text("Keep Mine")
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = { onResolve(Resolution.UseRemote) },
                modifier = Modifier.weight(1f)
            ) {
                Text("Use Server")
            }
        }
    }
}
```

## Cache Invalidation

Strategies to keep local cache fresh and consistent.

### Time-Based Invalidation

```kotlin
// core/data/cache/CacheManager.kt
@Singleton
class CacheManager @Inject constructor(
    private val preferencesDataSource: PreferencesDataSource
) {
    suspend fun isCacheValid(
        key: String,
        maxAge: Duration = 5.minutes
    ): Boolean {
        val lastUpdate = preferencesDataSource.getCacheTimestamp(key) ?: return false
        val age = Clock.System.now() - lastUpdate
        return age < maxAge
    }

    suspend fun markCacheUpdated(key: String) {
        preferencesDataSource.setCacheTimestamp(key, Clock.System.now())
    }

    suspend fun invalidateCache(key: String) {
        preferencesDataSource.removeCacheTimestamp(key)
    }
}

// Usage in Repository
override fun observeTasks(): Flow<List<Task>> = flow {
    // Emit cached data immediately
    emitAll(taskDao.observeAll().map { it.map(TaskEntity::toDomain) })
}.onStart {
    // Refresh if cache is stale
    if (!cacheManager.isCacheValid("tasks")) {
        refreshTasks()
    }
}

private suspend fun refreshTasks() {
    if (!networkMonitor.isConnected()) return
    
    try {
        val remoteTasks = taskApi.getTasks()
        taskDao.upsertAll(remoteTasks.map { it.toEntity() })
        cacheManager.markCacheUpdated("tasks")
    } catch (e: Exception) {
        // Log error but don't throw - UI still shows cached data
    }
}
```

### Event-Based Invalidation

```kotlin
// Invalidate when specific events occur
override suspend fun createTask(task: Task): Result<Task> = runCatching {
    taskDao.insert(task.toEntity())
    
    // Invalidate list cache since we added an item
    cacheManager.invalidateCache("tasks")
    
    syncCoordinator.scheduleSyncNow()
    task
}

override suspend fun deleteTask(id: String): Result<Unit> = runCatching {
    taskDao.markAsDeleted(id, Clock.System.now())
    
    // Invalidate both list and detail caches
    cacheManager.invalidateCache("tasks")
    cacheManager.invalidateCache("task_$id")
    
    syncCoordinator.scheduleSyncNow()
}
```

### Size-Based Invalidation (LRU Cache)

```kotlin
// For in-memory caches (images, etc.)
@Singleton
class ImageCacheManager @Inject constructor() {
    private val lruCache = object : LruCache<String, Bitmap>(
        maxSize = (Runtime.getRuntime().maxMemory() / 8).toInt()
    ) {
        override fun sizeOf(key: String, value: Bitmap): Int {
            return value.byteCount
        }
    }

    fun get(key: String): Bitmap? = lruCache.get(key)

    fun put(key: String, bitmap: Bitmap) {
        lruCache.put(key, bitmap)
    }

    fun evict(key: String) {
        lruCache.remove(key)
    }

    fun clear() {
        lruCache.evictAll()
    }
}
```

## Retry Mechanisms

Implement exponential backoff for transient failures.

### Retry with Exponential Backoff

```kotlin
// core/data/network/RetryStrategy.kt
interface RetryStrategy {
    suspend fun <T> retry(block: suspend () -> T): T
}

@Singleton
class ExponentialBackoffRetry @Inject constructor() : RetryStrategy {
    override suspend fun <T> retry(block: suspend () -> T): T {
        var currentDelay = 1.seconds
        val maxDelay = 32.seconds
        var attempts = 0
        val maxAttempts = 5

        while (true) {
            attempts++
            
            try {
                return block()
            } catch (e: Exception) {
                if (attempts >= maxAttempts) {
                    throw e
                }

                // Don't retry on client errors (4xx)
                if (e is HttpException && e.code() in 400..499) {
                    throw e
                }

                delay(currentDelay)
                currentDelay = (currentDelay * 2).coerceAtMost(maxDelay)
            }
        }
    }
}

// Usage in Repository
override suspend fun createTask(task: Task): Result<Task> = runCatching {
    // Save locally first (optimistic)
    val entity = task.toEntity().copy(syncStatus = SyncStatus.PENDING_CREATE)
    taskDao.insert(entity)
    
    // Try to sync immediately with retry
    if (networkMonitor.isConnected()) {
        retryStrategy.retry {
            val response = taskApi.createTask(task.toApiModel())
            taskDao.update(entity.copy(
                serverId = response.id,
                syncStatus = SyncStatus.SYNCED,
                serverVersion = response.version
            ))
        }
    }
    
    task
}.recoverCatching { e ->
    // If immediate sync fails, WorkManager will retry later
    task
}
```

### Configurable Retry Policy

```kotlin
data class RetryPolicy(
    val maxAttempts: Int = 5,
    val initialDelay: Duration = 1.seconds,
    val maxDelay: Duration = 32.seconds,
    val backoffMultiplier: Double = 2.0,
    val retryableErrors: Set<Int> = setOf(408, 429, 500, 502, 503, 504)
)

class ConfigurableRetry @Inject constructor(
    private val policy: RetryPolicy
) : RetryStrategy {
    override suspend fun <T> retry(block: suspend () -> T): T {
        var currentDelay = policy.initialDelay
        var attempts = 0

        while (true) {
            attempts++
            
            try {
                return block()
            } catch (e: Exception) {
                if (attempts >= policy.maxAttempts) {
                    throw e
                }

                if (e is HttpException && e.code() !in policy.retryableErrors) {
                    throw e
                }

                delay(currentDelay)
                currentDelay = (currentDelay * policy.backoffMultiplier)
                    .coerceAtMost(policy.maxDelay)
            }
        }
    }
}
```

### Retry with Jitter

Prevent thundering herd problem by adding randomness:

```kotlin
@Singleton
class JitteredRetry @Inject constructor() : RetryStrategy {
    private val random = Random.Default

    override suspend fun <T> retry(block: suspend () -> T): T {
        var baseDelay = 1.seconds
        val maxDelay = 32.seconds
        var attempts = 0
        val maxAttempts = 5

        while (true) {
            attempts++
            
            try {
                return block()
            } catch (e: Exception) {
                if (attempts >= maxAttempts) throw e
                if (e is HttpException && e.code() in 400..499) throw e

                // Add jitter: randomize between 0 and baseDelay
                val jitter = random.nextDouble(0.0, baseDelay.inWholeMilliseconds.toDouble())
                delay(jitter.toLong().milliseconds)
                
                baseDelay = (baseDelay * 2).coerceAtMost(maxDelay)
            }
        }
    }
}
```

## WorkManager Integration

Schedule background sync with WorkManager for reliable execution.

### Sync Coordinator

```kotlin
// core/sync/SyncCoordinator.kt
interface SyncCoordinator {
    fun scheduleSyncNow()
    fun schedulePeriodicSync()
    fun cancelSync()
}

@Singleton
class WorkManagerSyncCoordinator @Inject constructor(
    @ApplicationContext private val context: Context
) : SyncCoordinator {

    private val workManager = WorkManager.getInstance(context)

    override fun scheduleSyncNow() {
        val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                WorkRequest.MIN_BACKOFF_MILLIS,
                TimeUnit.MILLISECONDS
            )
            .build()

        workManager.enqueueUniqueWork(
            "sync_now",
            ExistingWorkPolicy.REPLACE,
            syncRequest
        )
    }

    override fun schedulePeriodicSync() {
        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
            repeatInterval = 1,
            repeatIntervalTimeUnit = TimeUnit.HOURS,
            flexTimeInterval = 15,
            flexTimeIntervalUnit = TimeUnit.MINUTES
        )
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .setRequiresBatteryNotLow(true)
                    .build()
            )
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                WorkRequest.MIN_BACKOFF_MILLIS,
                TimeUnit.MILLISECONDS
            )
            .build()

        workManager.enqueueUniquePeriodicWork(
            "periodic_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )
    }

    override fun cancelSync() {
        workManager.cancelUniqueWork("sync_now")
        workManager.cancelUniqueWork("periodic_sync")
    }

    fun observeSyncStatus(): Flow<WorkInfo?> {
        return workManager.getWorkInfosForUniqueWorkFlow("sync_now")
            .map { workInfos -> workInfos.firstOrNull() }
    }
}
```

### Initialize Periodic Sync in Application

```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var syncCoordinator: SyncCoordinator

    override fun onCreate() {
        super.onCreate()
        
        // Schedule periodic background sync
        syncCoordinator.schedulePeriodicSync()
    }
}
```

### Work Constraints

WorkManager supports various constraints to control when work executes:

```kotlin
fun scheduleSmartSync() {
    val constraints = Constraints.Builder()
        // Network constraints
        .setRequiredNetworkType(NetworkType.CONNECTED) // Any network
        // .setRequiredNetworkType(NetworkType.UNMETERED) // WiFi only
        // .setRequiredNetworkType(NetworkType.NOT_ROAMING) // No roaming
        
        // Battery constraints
        .setRequiresBatteryNotLow(true) // Battery above critical level
        // .setRequiresCharging(true) // Device charging (API 23+)
        
        // Storage constraint
        .setRequiresStorageNotLow(true) // Sufficient storage space
        
        // Device state (API 23+)
        // .setRequiresDeviceIdle(true) // Device idle (for heavy operations)
        
        .build()

    val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
        .setConstraints(constraints)
        .build()

    workManager.enqueue(syncRequest)
}
```

### Work Chaining

Chain multiple work requests for sequential or parallel execution:

#### Sequential Work Chain

```kotlin
fun scheduleFullDataSync() {
    // Step 1: Clean up old data
    val cleanupWork = OneTimeWorkRequestBuilder<CleanupWorker>()
        .build()

    // Step 2: Download new data
    val downloadWork = OneTimeWorkRequestBuilder<DownloadWorker>()
        .build()

    // Step 3: Process downloaded data
    val processWork = OneTimeWorkRequestBuilder<ProcessWorker>()
        .build()

    // Chain: cleanup → download → process
    workManager
        .beginUniqueWork(
            "full_sync",
            ExistingWorkPolicy.REPLACE,
            cleanupWork
        )
        .then(downloadWork)
        .then(processWork)
        .enqueue()
}
```

#### Parallel Work with Join

```kotlin
fun syncAllDataTypes() {
    // Sync different data types in parallel
    val syncTasks = OneTimeWorkRequestBuilder<TaskSyncWorker>().build()
    val syncProjects = OneTimeWorkRequestBuilder<ProjectSyncWorker>().build()
    val syncUsers = OneTimeWorkRequestBuilder<UserSyncWorker>().build()

    // Final work after all complete
    val notifyComplete = OneTimeWorkRequestBuilder<NotifyCompleteWorker>().build()

    // Run tasks, projects, users in parallel, then notify
    workManager
        .beginWith(listOf(syncTasks, syncProjects, syncUsers))
        .then(notifyComplete)
        .enqueue()
}
```

#### Complex Chain with Fan-Out/Fan-In

```kotlin
fun syncWithBackupAndCleanup() {
    // Initial work
    val prepareWork = OneTimeWorkRequestBuilder<PrepareWorker>().build()

    // Parallel operations after prepare
    val syncWork = OneTimeWorkRequestBuilder<SyncWorker>().build()
    val backupWork = OneTimeWorkRequestBuilder<BackupWorker>().build()

    // Final cleanup after both complete
    val cleanupWork = OneTimeWorkRequestBuilder<CleanupWorker>().build()

    workManager
        .beginWith(prepareWork)
        .then(listOf(syncWork, backupWork)) // Fan out
        .then(cleanupWork) // Fan in
        .enqueue()
}
```

### Passing Data Between Workers

Use `Data` to pass information between chained workers:

```kotlin
// First worker outputs data
@HiltWorker
class DownloadWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val dataApi: DataApi
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            val data = dataApi.downloadData()
            
            // Output data for next worker
            val outputData = Data.Builder()
                .putInt("downloaded_count", data.size)
                .putString("download_timestamp", Clock.System.now().toString())
                .putStringArray("item_ids", data.map { it.id }.toTypedArray())
                .build()

            Result.success(outputData)
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

// Second worker reads input data
@HiltWorker
class ProcessWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val processor: DataProcessor
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        // Read data from previous worker
        val itemCount = inputData.getInt("downloaded_count", 0)
        val timestamp = inputData.getString("download_timestamp")
        val itemIds = inputData.getStringArray("item_ids")

        if (itemIds == null || itemIds.isEmpty()) {
            return Result.failure()
        }

        return try {
            processor.processItems(itemIds.toList())
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
```

### Progress Updates

Report progress for long-running operations:

```kotlin
@HiltWorker
class LargeDataSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val taskRepository: TaskRepository
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val tasks = taskRepository.getPendingSync()
        val totalTasks = tasks.size

        if (totalTasks == 0) {
            return Result.success()
        }

        // Use setForeground for expedited work (API 31+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            setForeground(createForegroundInfo())
        }

        tasks.forEachIndexed { index, task ->
            try {
                taskRepository.syncTask(task)
                
                // Update progress
                val progress = ((index + 1) * 100) / totalTasks
                setProgress(
                    Data.Builder()
                        .putInt("progress", progress)
                        .putInt("synced", index + 1)
                        .putInt("total", totalTasks)
                        .build()
                )
            } catch (e: Exception) {
                // Continue with next task
            }
        }

        return Result.success()
    }

    private fun createForegroundInfo(): ForegroundInfo {
        val notification = NotificationCompat.Builder(
            applicationContext,
            NotificationChannels.CHANNEL_FOREGROUND_SERVICE
        )
            .setSmallIcon(R.drawable.ic_sync)
            .setContentTitle("Syncing data")
            .setOngoing(true)
            .build()

        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ForegroundInfo(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            ForegroundInfo(NOTIFICATION_ID, notification)
        }
    }

    companion object {
        private const val NOTIFICATION_ID = 2001
    }
}

// Observe progress in ViewModel
val syncProgress: StateFlow<SyncProgress> = workManager
    .getWorkInfoByIdFlow(workId)
    .map { workInfo ->
        val progress = workInfo?.progress?.getInt("progress", 0) ?: 0
        val synced = workInfo?.progress?.getInt("synced", 0) ?: 0
        val total = workInfo?.progress?.getInt("total", 0) ?: 0
        
        SyncProgress(
            percentage = progress,
            itemsSynced = synced,
            totalItems = total
        )
    }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = SyncProgress(0, 0, 0)
    )
```

### Observing Work Status

Monitor work state and handle completion:

```kotlin
// Observe single work request
fun observeWorkStatus(workId: UUID): Flow<WorkInfo?> {
    return workManager.getWorkInfoByIdFlow(workId)
}

// Observe unique work by name
fun observeSyncWork(): Flow<WorkInfo?> {
    return workManager.getWorkInfosForUniqueWorkFlow("sync_now")
        .map { workInfos -> workInfos.firstOrNull() }
}

// Observe work by tag
fun observeTaggedWork(tag: String): Flow<List<WorkInfo>> {
    return workManager.getWorkInfosByTagFlow(tag)
}

// Use in ViewModel
val syncState: StateFlow<SyncState> = syncCoordinator.observeSyncStatus()
    .map { workInfo ->
        when (workInfo?.state) {
            WorkInfo.State.ENQUEUED -> SyncState.Pending
            WorkInfo.State.RUNNING -> SyncState.Syncing
            WorkInfo.State.SUCCEEDED -> SyncState.Success
            WorkInfo.State.FAILED -> {
                val error = workInfo.outputData.getString("error") ?: "Unknown error"
                SyncState.Error(error)
            }
            WorkInfo.State.BLOCKED -> SyncState.Blocked
            WorkInfo.State.CANCELLED -> SyncState.Cancelled
            else -> SyncState.Idle
        }
    }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = SyncState.Idle
    )
```

### Expedited Work (API 31+)

For time-sensitive operations that need to run immediately:

```kotlin
fun scheduleExpeditedSync() {
    val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
        .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
        .setConstraints(
            Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
        )
        .build()

    workManager.enqueue(syncRequest)
}
```

### Testing WorkManager

#### Testing with TestDriver

```kotlin
// core/sync/SyncWorkerTest.kt
@RunWith(AndroidJUnit4::class)
class SyncWorkerTest {
    private lateinit var context: Context
    private lateinit var workManager: WorkManager
    private lateinit var testDriver: TestDriver

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
        
        // Initialize WorkManager for tests
        val config = Configuration.Builder()
            .setMinimumLoggingLevel(Log.DEBUG)
            .setExecutor(SynchronousExecutor())
            .build()
        
        WorkManagerTestInitHelper.initializeTestWorkManager(context, config)
        
        workManager = WorkManager.getInstance(context)
        testDriver = WorkManagerTestInitHelper.getTestDriver(context)!!
    }

    @Test
    fun syncWorker_successfulSync_returnsSuccess() = runTest {
        // Setup
        val fakeRepository = FakeTaskRepository()
        fakeRepository.setTasks(listOf(
            Task("1", "Task 1", null, TaskStatus.TODO)
        ))

        // Create work request
        val request = OneTimeWorkRequestBuilder<SyncWorker>()
            .build()

        // Enqueue work
        workManager.enqueue(request).result.get()

        // Simulate constraints met
        testDriver.setAllConstraintsMet(request.id)

        // Wait for work to complete
        val workInfo = workManager.getWorkInfoById(request.id).get()

        // Assert
        assertThat(workInfo.state).isEqualTo(WorkInfo.State.SUCCEEDED)
    }

    @Test
    fun syncWorker_noNetwork_retriesWork() = runTest {
        val fakeNetworkMonitor = FakeNetworkMonitor()
        fakeNetworkMonitor.setConnected(false)

        val request = OneTimeWorkRequestBuilder<SyncWorker>()
            .build()

        workManager.enqueue(request).result.get()
        testDriver.setAllConstraintsMet(request.id)

        val workInfo = workManager.getWorkInfoById(request.id).get()

        assertThat(workInfo.state).isEqualTo(WorkInfo.State.ENQUEUED)
        assertThat(workInfo.runAttemptCount).isGreaterThan(0)
    }

    @Test
    fun syncWorker_updatesProgress() = runTest {
        val request = OneTimeWorkRequestBuilder<LargeDataSyncWorker>()
            .build()

        workManager.enqueue(request).result.get()
        testDriver.setAllConstraintsMet(request.id)

        // Collect progress updates
        val progressValues = mutableListOf<Int>()
        
        workManager.getWorkInfoByIdFlow(request.id)
            .take(5)
            .collect { workInfo ->
                workInfo?.progress?.getInt("progress", -1)?.let {
                    if (it >= 0) progressValues.add(it)
                }
            }

        assertThat(progressValues).isNotEmpty()
        assertThat(progressValues.last()).isEqualTo(100)
    }
}
```

#### Testing Work Chains

```kotlin
@Test
fun workChain_executesSequentially() = runTest {
    val cleanup = OneTimeWorkRequestBuilder<CleanupWorker>().build()
    val download = OneTimeWorkRequestBuilder<DownloadWorker>().build()
    val process = OneTimeWorkRequestBuilder<ProcessWorker>().build()

    // Enqueue chain
    workManager
        .beginWith(cleanup)
        .then(download)
        .then(process)
        .enqueue()
        .result
        .get()

    // Drive all constraints
    testDriver.setAllConstraintsMet(cleanup.id)
    testDriver.setAllConstraintsMet(download.id)
    testDriver.setAllConstraintsMet(process.id)

    // Verify execution order
    val cleanupInfo = workManager.getWorkInfoById(cleanup.id).get()
    val downloadInfo = workManager.getWorkInfoById(download.id).get()
    val processInfo = workManager.getWorkInfoById(process.id).get()

    assertThat(cleanupInfo.state).isEqualTo(WorkInfo.State.SUCCEEDED)
    assertThat(downloadInfo.state).isEqualTo(WorkInfo.State.SUCCEEDED)
    assertThat(processInfo.state).isEqualTo(WorkInfo.State.SUCCEEDED)
}

@Test
fun workChain_failureStopsChain() = runTest {
    val fakeDownloader = FakeDownloader()
    fakeDownloader.setShouldFail(true)

    val download = OneTimeWorkRequestBuilder<DownloadWorker>().build()
    val process = OneTimeWorkRequestBuilder<ProcessWorker>().build()

    workManager
        .beginWith(download)
        .then(process)
        .enqueue()
        .result
        .get()

    testDriver.setAllConstraintsMet(download.id)

    val downloadInfo = workManager.getWorkInfoById(download.id).get()
    val processInfo = workManager.getWorkInfoById(process.id).get()

    // Download failed, so process should be cancelled
    assertThat(downloadInfo.state).isEqualTo(WorkInfo.State.FAILED)
    assertThat(processInfo.state).isEqualTo(WorkInfo.State.CANCELLED)
}
```

#### Fake SyncCoordinator

```kotlin
// core/testing/FakeSyncCoordinator.kt
class FakeSyncCoordinator : SyncCoordinator {
    private val _workInfoFlow = MutableStateFlow<WorkInfo?>(null)
    
    var syncScheduled = false
        private set
    
    var periodicSyncScheduled = false
        private set
    
    var syncCancelled = false
        private set

    override fun scheduleSyncNow() {
        syncScheduled = true
        _workInfoFlow.value = createWorkInfo(WorkInfo.State.ENQUEUED)
    }

    override fun schedulePeriodicSync() {
        periodicSyncScheduled = true
    }

    override fun cancelSync() {
        syncCancelled = true
        _workInfoFlow.value = createWorkInfo(WorkInfo.State.CANCELLED)
    }

    fun observeSyncStatus(): Flow<WorkInfo?> = _workInfoFlow.asStateFlow()

    fun setWorkState(state: WorkInfo.State) {
        _workInfoFlow.value = createWorkInfo(state)
    }

    private fun createWorkInfo(state: WorkInfo.State): WorkInfo {
        // Create a mock WorkInfo for testing
        return mock<WorkInfo>().apply {
            whenever(this.state).thenReturn(state)
        }
    }

    fun reset() {
        syncScheduled = false
        periodicSyncScheduled = false
        syncCancelled = false
        _workInfoFlow.value = null
    }
}
```

### WorkManager Best Practices

#### ✅ Do

1. **Use unique work names** for sync operations to prevent duplicates
2. **Set appropriate constraints** to respect user's battery and data
3. **Handle backoff** for transient failures
4. **Use expedited work** (API 31+) for time-sensitive operations
5. **Report progress** for long-running work
6. **Chain work** for complex multi-step operations
7. **Pass data** between workers using `Data.Builder()`
8. **Observe work status** in ViewModel, not composables
9. **Test with TestDriver** to simulate constraint changes
10. **Cancel work** when no longer needed

#### ❌ Don't

1. **Don't use WorkManager for immediate execution** - use coroutines instead
2. **Don't store large data in Worker input/output** - max 10KB per Data object
3. **Don't rely on Worker lifecycle** - work can be interrupted and restarted
4. **Don't use periodic work with flex < 15 minutes** - system constraint
5. **Don't forget to cancel periodic work** when feature is disabled
6. **Don't chain too many workers** - prefer batching in single worker
7. **Don't use expedited work unnecessarily** - limited quota
8. **Don't block main thread** in Worker - use CoroutineWorker
9. **Don't assume work will run immediately** - constraints must be met
10. **Don't use WorkManager for UI updates** - use StateFlow/LiveData

### Work Constraints Comparison

| Constraint | Use Case | Example |
|------------|----------|---------|
| `NetworkType.CONNECTED` | Any data sync | General API calls |
| `NetworkType.UNMETERED` | Large downloads | Media sync, backups |
| `NetworkType.NOT_ROAMING` | Cost-sensitive ops | International users |
| `requiresBatteryNotLow` | Background sync | Periodic updates |
| `requiresCharging` | Heavy operations | Database cleanup, indexing |
| `requiresStorageNotLow` | Downloads | Media, cache management |
| `requiresDeviceIdle` | Very heavy ops | Full database rebuild |

## Repository Pattern for Sync

Complete repository example integrating all patterns.

```kotlin
// core/domain/TaskRepository.kt
interface TaskRepository {
    fun observeTasks(): Flow<List<Task>>
    fun observeTask(id: String): Flow<Task?>
    suspend fun createTask(task: Task): Result<Task>
    suspend fun updateTask(task: Task): Result<Task>
    suspend fun deleteTask(id: String): Result<Unit>
    suspend fun syncBidirectional(): SyncResult
    suspend fun refreshTasks(): Result<Unit>
}

// core/data/TaskRepositoryImpl.kt (complete implementation)
@Singleton
class TaskRepositoryImpl @Inject constructor(
    private val taskDao: TaskDao,
    private val taskApi: TaskApi,
    private val networkMonitor: NetworkMonitor,
    private val syncCoordinator: SyncCoordinator,
    private val retryStrategy: RetryStrategy,
    private val cacheManager: CacheManager
) : TaskRepository {

    override fun observeTasks(): Flow<List<Task>> = taskDao.observeAll()
        .map { entities -> entities.map { it.toDomain() } }
        .onStart {
            if (!cacheManager.isCacheValid("tasks", maxAge = 5.minutes)) {
                refreshTasks()
            }
        }

    override fun observeTask(id: String): Flow<Task?> = taskDao.observeById(id)
        .map { it?.toDomain() }

    override suspend fun createTask(task: Task): Result<Task> = runCatching {
        val entity = task.toEntity().copy(
            syncStatus = SyncStatus.PENDING_CREATE,
            lastModified = Clock.System.now()
        )
        taskDao.insert(entity)
        cacheManager.invalidateCache("tasks")
        syncCoordinator.scheduleSyncNow()
        task
    }

    override suspend fun updateTask(task: Task): Result<Task> = runCatching {
        val entity = task.toEntity().copy(
            syncStatus = SyncStatus.PENDING_UPDATE,
            lastModified = Clock.System.now()
        )
        taskDao.update(entity)
        cacheManager.invalidateCache("tasks")
        cacheManager.invalidateCache("task_${task.id}")
        syncCoordinator.scheduleSyncNow()
        task
    }

    override suspend fun deleteTask(id: String): Result<Unit> = runCatching {
        taskDao.markAsDeleted(id, Clock.System.now())
        cacheManager.invalidateCache("tasks")
        cacheManager.invalidateCache("task_$id")
        syncCoordinator.scheduleSyncNow()
    }

    override suspend fun syncBidirectional(): SyncResult {
        if (!networkMonitor.isConnected()) {
            return SyncResult.NoNetwork
        }

        return coroutineScope {
            val pushJob = async { pushLocalChanges() }
            val pullJob = async { pullRemoteChanges() }

            val pushResult = pushJob.await()
            val pullResult = pullJob.await()

            when {
                pushResult is SyncResult.Success && pullResult is SyncResult.Success -> {
                    cacheManager.markCacheUpdated("tasks")
                    SyncResult.Success(
                        pushResult.itemsSynced + pullResult.itemsSynced
                    )
                }
                else -> SyncResult.PartialSuccess(
                    successCount = 0,
                    failures = emptyList()
                )
            }
        }
    }

    override suspend fun refreshTasks(): Result<Unit> = runCatching {
        if (!networkMonitor.isConnected()) {
            return Result.success(Unit)
        }

        retryStrategy.retry {
            val remoteTasks = taskApi.getTasks()
            val entities = remoteTasks.map { it.toEntity() }
            taskDao.upsertAll(entities)
            cacheManager.markCacheUpdated("tasks")
        }
    }

    private suspend fun pushLocalChanges(): SyncResult {
        val pending = taskDao.getPendingSync()
        val results = pending.map { task ->
            when (task.syncStatus) {
                SyncStatus.PENDING_CREATE -> syncCreate(task)
                SyncStatus.PENDING_UPDATE -> syncUpdate(task)
                SyncStatus.PENDING_DELETE -> syncDelete(task)
                else -> SyncItemResult.Success(task.id)
            }
        }

        return if (results.all { it is SyncItemResult.Success }) {
            SyncResult.Success(results.size)
        } else {
            SyncResult.PartialSuccess(
                successCount = results.count { it is SyncItemResult.Success },
                failures = results.filterIsInstance<SyncItemResult.Failed>()
            )
        }
    }

    private suspend fun pullRemoteChanges(): SyncResult = runCatching {
        val lastSync = cacheManager.getLastSyncTime("tasks")
        val remoteTasks = taskApi.getTasksSince(lastSync)

        remoteTasks.forEach { apiTask ->
            val local = taskDao.getByServerId(apiTask.id)
            
            when {
                local == null -> taskDao.insert(apiTask.toEntity())
                local.syncStatus == SyncStatus.SYNCED -> {
                    taskDao.update(local.copy(
                        title = apiTask.title,
                        description = apiTask.description,
                        status = apiTask.status,
                        serverVersion = apiTask.version,
                        lastModified = apiTask.updatedAt
                    ))
                }
                else -> resolveConflict(local, apiTask)
            }
        }

        SyncResult.Success(remoteTasks.size)
    }.getOrElse { e ->
        SyncResult.Error(e.message ?: "Pull failed")
    }

    private suspend fun syncCreate(task: TaskEntity): SyncItemResult = try {
        retryStrategy.retry {
            val response = taskApi.createTask(task.toApiModel())
            taskDao.update(task.copy(
                serverId = response.id,
                syncStatus = SyncStatus.SYNCED,
                serverVersion = response.version
            ))
        }
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun syncUpdate(task: TaskEntity): SyncItemResult = try {
        retryStrategy.retry {
            val response = taskApi.updateTask(task.serverId!!, task.toApiModel())
            
            if (response.version <= task.serverVersion) {
                return@retry resolveConflict(task, response)
            }
            
            taskDao.update(task.copy(
                syncStatus = SyncStatus.SYNCED,
                serverVersion = response.version
            ))
        }
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun syncDelete(task: TaskEntity): SyncItemResult = try {
        retryStrategy.retry {
            taskApi.deleteTask(task.serverId!!)
            taskDao.delete(task.id)
        }
        SyncItemResult.Success(task.id)
    } catch (e: Exception) {
        handleSyncError(task, e)
    }

    private suspend fun handleSyncError(
        task: TaskEntity,
        error: Exception
    ): SyncItemResult {
        return when {
            error is HttpException && error.code() == 409 -> {
                SyncItemResult.Conflict(task.id, error.message())
            }
            error is HttpException && error.code() in 400..499 -> {
                taskDao.update(task.copy(syncStatus = SyncStatus.FAILED))
                SyncItemResult.Failed(task.id, error.message())
            }
            else -> {
                SyncItemResult.Retry(task.id, error.message ?: "Unknown error")
            }
        }
    }

    private suspend fun resolveConflict(
        local: TaskEntity,
        remote: ApiTask
    ): SyncItemResult {
        // Server wins strategy
        taskDao.update(local.copy(
            title = remote.title,
            description = remote.description,
            status = remote.status,
            serverVersion = remote.version,
            syncStatus = SyncStatus.SYNCED,
            lastModified = remote.updatedAt
        ))
        return SyncItemResult.ConflictResolved(local.id, "Server version applied")
    }
}
```

## Architecture Integration

### ViewModel Observing Sync State

```kotlin
// feature/tasks/presentation/TasksViewModel.kt
@HiltViewModel
class TasksViewModel @Inject constructor(
    private val taskRepository: TaskRepository,
    private val syncCoordinator: SyncCoordinator
) : ViewModel() {

    val tasks: StateFlow<List<Task>> = taskRepository.observeTasks()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList()
        )

    val syncState: StateFlow<SyncState> = syncCoordinator.observeSyncStatus()
        .map { workInfo ->
            when (workInfo?.state) {
                WorkInfo.State.RUNNING -> SyncState.Syncing
                WorkInfo.State.SUCCEEDED -> SyncState.Success
                WorkInfo.State.FAILED -> SyncState.Error("Sync failed")
                else -> SyncState.Idle
            }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = SyncState.Idle
        )

    fun syncNow() {
        syncCoordinator.scheduleSyncNow()
    }

    fun createTask(title: String) {
        viewModelScope.launch {
            val task = Task(
                id = generateId(),
                title = title,
                description = null,
                status = TaskStatus.TODO
            )
            taskRepository.createTask(task)
        }
    }
}

sealed interface SyncState {
    data object Idle : SyncState
    data object Syncing : SyncState
    data object Success : SyncState
    data class Error(val message: String) : SyncState
}
```

### UI Displaying Sync Status

```kotlin
@Composable
fun TasksScreen(
    viewModel: TasksViewModel = hiltViewModel()
) {
    val tasks by viewModel.tasks.collectAsStateWithLifecycle()
    val syncState by viewModel.syncState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Tasks") },
                actions = {
                    SyncButton(
                        syncState = syncState,
                        onSyncClick = { viewModel.syncNow() }
                    )
                }
            )
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            // Show sync indicator
            when (syncState) {
                is SyncState.Syncing -> LinearProgressIndicator(
                    modifier = Modifier.fillMaxWidth()
                )
                is SyncState.Error -> {
                    Text(
                        text = (syncState as SyncState.Error).message,
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(16.dp)
                    )
                }
                else -> {}
            }

            LazyColumn {
                items(tasks, key = { it.id }) { task ->
                    TaskItem(task = task)
                }
            }
        }
    }
}

@Composable
fun SyncButton(
    syncState: SyncState,
    onSyncClick: () -> Unit
) {
    IconButton(
        onClick = onSyncClick,
        enabled = syncState !is SyncState.Syncing
    ) {
        when (syncState) {
            is SyncState.Syncing -> {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    strokeWidth = 2.dp
                )
            }
            else -> {
                Icon(
                    painter = painterResource(R.drawable.ic_sync),
                    contentDescription = "Sync"
                )
            }
        }
    }
}
```

## Testing

### Fake Repository

```kotlin
// core/testing/FakeTaskRepository.kt
class FakeTaskRepository : TaskRepository {
    private val _tasks = MutableStateFlow<List<Task>>(emptyList())
    private var shouldFailSync = false
    private var syncDelay = Duration.ZERO

    override fun observeTasks(): Flow<List<Task>> = _tasks.asStateFlow()

    override fun observeTask(id: String): Flow<Task?> = _tasks
        .map { tasks -> tasks.find { it.id == id } }

    override suspend fun createTask(task: Task): Result<Task> = runCatching {
        _tasks.value = _tasks.value + task
        task
    }

    override suspend fun updateTask(task: Task): Result<Task> = runCatching {
        _tasks.value = _tasks.value.map {
            if (it.id == task.id) task else it
        }
        task
    }

    override suspend fun deleteTask(id: String): Result<Unit> = runCatching {
        _tasks.value = _tasks.value.filterNot { it.id == id }
    }

    override suspend fun syncBidirectional(): SyncResult {
        delay(syncDelay)
        
        return if (shouldFailSync) {
            SyncResult.Error("Sync failed")
        } else {
            SyncResult.Success(_tasks.value.size)
        }
    }

    override suspend fun refreshTasks(): Result<Unit> = runCatching {
        // No-op for fake
    }

    fun setShouldFailSync(shouldFail: Boolean) {
        shouldFailSync = shouldFail
    }

    fun setSyncDelay(delay: Duration) {
        syncDelay = delay
    }

    fun setTasks(tasks: List<Task>) {
        _tasks.value = tasks
    }
}
```

### Fake Network Monitor

```kotlin
// core/testing/FakeNetworkMonitor.kt
class FakeNetworkMonitor : NetworkMonitor {
    private val _isConnected = MutableStateFlow(true)
    override val isConnected: Flow<Boolean> = _isConnected.asStateFlow()

    override suspend fun isConnected(): Boolean = _isConnected.value

    fun setConnected(connected: Boolean) {
        _isConnected.value = connected
    }
}
```

### Testing Sync Logic

```kotlin
// core/data/TaskRepositoryTest.kt
@Test
fun `syncBidirectional returns NoNetwork when offline`() = runTest {
    val fakeNetworkMonitor = FakeNetworkMonitor()
    fakeNetworkMonitor.setConnected(false)
    
    val repository = TaskRepositoryImpl(
        taskDao = fakeTaskDao,
        taskApi = fakeTaskApi,
        networkMonitor = fakeNetworkMonitor,
        syncCoordinator = fakeSyncCoordinator,
        retryStrategy = fakeRetryStrategy,
        cacheManager = fakeCacheManager
    )

    val result = repository.syncBidirectional()

    assertThat(result).isEqualTo(SyncResult.NoNetwork)
}

@Test
fun `createTask writes to local database and schedules sync`() = runTest {
    val repository = TaskRepositoryImpl(/* ... */)
    val task = Task(id = "1", title = "Test", description = null, status = TaskStatus.TODO)

    repository.createTask(task)

    val saved = fakeTaskDao.getById("1")
    assertThat(saved).isNotNull()
    assertThat(saved?.syncStatus).isEqualTo(SyncStatus.PENDING_CREATE)
    verify(fakeSyncCoordinator).scheduleSyncNow()
}

@Test
fun `conflict resolution applies server version when strategy is ServerWins`() = runTest {
    // Setup local task with pending changes
    val localTask = TaskEntity(
        id = "1",
        serverId = "server-1",
        title = "Local Title",
        description = null,
        status = TaskStatus.TODO,
        syncStatus = SyncStatus.PENDING_UPDATE,
        lastModified = Clock.System.now(),
        serverVersion = 1
    )
    fakeTaskDao.insert(localTask)

    // Server has newer version
    val remoteTask = ApiTask(
        id = "server-1",
        title = "Server Title",
        description = null,
        status = TaskStatus.IN_PROGRESS,
        version = 2,
        updatedAt = Clock.System.now()
    )
    fakeTaskApi.setMockResponse(remoteTask)

    val repository = TaskRepositoryImpl(/* ... */)
    repository.syncBidirectional()

    val updated = fakeTaskDao.getById("1")
    assertThat(updated?.title).isEqualTo("Server Title")
    assertThat(updated?.status).isEqualTo(TaskStatus.IN_PROGRESS)
    assertThat(updated?.syncStatus).isEqualTo(SyncStatus.SYNCED)
}
```

### Testing ViewModel with Sync

```kotlin
// feature/tasks/presentation/TasksViewModelTest.kt
@Test
fun `syncNow triggers sync coordinator`() = runTest {
    val fakeSyncCoordinator = FakeSyncCoordinator()
    val viewModel = TasksViewModel(
        taskRepository = fakeTaskRepository,
        syncCoordinator = fakeSyncCoordinator
    )

    viewModel.syncNow()

    assertThat(fakeSyncCoordinator.syncScheduled).isTrue()
}

@Test
fun `syncState reflects WorkInfo state`() = runTest {
    val workInfoFlow = MutableStateFlow<WorkInfo?>(null)
    val fakeSyncCoordinator = FakeSyncCoordinator()
    fakeSyncCoordinator.setWorkInfoFlow(workInfoFlow)
    
    val viewModel = TasksViewModel(
        taskRepository = fakeTaskRepository,
        syncCoordinator = fakeSyncCoordinator
    )

    // Initially idle
    assertThat(viewModel.syncState.value).isEqualTo(SyncState.Idle)

    // Simulate running
    workInfoFlow.value = WorkInfo(/* state = RUNNING */)
    advanceUntilIdle()
    assertThat(viewModel.syncState.value).isEqualTo(SyncState.Syncing)

    // Simulate success
    workInfoFlow.value = WorkInfo(/* state = SUCCEEDED */)
    advanceUntilIdle()
    assertThat(viewModel.syncState.value).isEqualTo(SyncState.Success)
}
```

## Best Practices

### ✅ Always Do

1. **Use local database as source of truth** - UI always observes local data
2. **Write locally first (optimistic updates)** - Don't wait for network
3. **Schedule background sync** with WorkManager for reliability
4. **Monitor network state** before attempting sync
5. **Implement conflict resolution** for diverging changes
6. **Use exponential backoff** for retries to avoid overwhelming server
7. **Add sync metadata** to entities (syncStatus, lastModified, serverVersion)
8. **Invalidate caches** when data changes
9. **Handle partial sync failures** gracefully
10. **Test offline scenarios** - disable network in tests

### ❌ Never Do

1. **Never block UI** waiting for network operations
2. **Never show stale data** - always emit cached data first, then refresh
3. **Never lose user data** - persist locally even if sync fails
4. **Never retry indefinitely** - set max retry limits
5. **Never ignore conflicts** - implement proper resolution strategy
6. **Never sync on metered connections** without user consent
7. **Never assume sync will succeed** - handle failures gracefully
8. **Never expose repository sync details** to UI - use ViewModel layer
9. **Never use SharedPreferences** for large datasets (use Room)
10. **Never forget to cancel coroutines** in repository when scope is cancelled

### Sync Frequency Guidelines

- **Critical data**: Sync immediately + periodic (15 min)
- **User-generated content**: Sync immediately on create/update/delete
- **Feed/timeline**: Periodic (30-60 min) + manual refresh
- **Profile data**: On app start + manual refresh
- **Settings**: Sync immediately on change

### Conflict Resolution Strategy Selection

| Scenario              | Strategy          | Reason                         |
|-----------------------|-------------------|--------------------------------|
| User preferences      | Client wins       | User's device is authoritative |
| Shared documents      | Last write wins   | Simple, works for most cases   |
| Collaborative editing | Manual resolution | Preserve both versions         |
| Server-managed data   | Server wins       | Server is authoritative        |

### Performance Considerations

- **Batch operations**: Sync multiple items in one request
- **Delta sync**: Only sync changed items since last sync
- **Pagination**: Don't load entire dataset at once
- **Compression**: Compress large payloads
- **Background threads**: All sync operations on IO dispatcher

## References

- [Repository Pattern - Android Developers](https://developer.android.com/topic/architecture/data-layer)
- [Offline-First Architecture - Android Developers](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [WorkManager - Android Developers](https://developer.android.com/topic/libraries/architecture/workmanager)
- [Room Database](https://developer.android.com/training/data-storage/room)
- [ConnectivityManager](https://developer.android.com/reference/android/net/ConnectivityManager)
- [Network Callbacks](https://developer.android.com/training/monitoring-device-state/connectivity-status-type)
- [Exponential Backoff](https://cloud.google.com/iot/docs/how-tos/exponential-backoff)
