# Android Notifications

Modern notification patterns following Material Design 3 guidelines with proper channel management, actions, and foreground services.

All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

**Related guides:** 
- See `references/android-permissions.md` for POST_NOTIFICATIONS permission handling
- See `references/android-data-sync.md` for WorkManager background sync patterns

## Table of Contents

- [Notification Channels (API 26+)](#notification-channels-api-26)
- [Basic Notifications](#basic-notifications)
- [Notification Styles](#notification-styles)
- [Action Buttons](#action-buttons)
- [Progress Notifications](#progress-notifications)
- [Progress-Centric Notifications (API 36+)](#progress-centric-notifications-api-36)
- [Foreground Service Notifications](#foreground-service-notifications)
- [Notification Manager Interface](#notification-manager-interface)
- [Architecture Integration](#architecture-integration)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Notification Channels (API 26+)

Notification channels are **required** for API 26+ but are no-ops on API 24-25.

### Channel Creation

Create channels once at app startup:

```kotlin
// core/notifications/NotificationChannels.kt
package com.example.core.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationManagerCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationChannels @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        const val CHANNEL_GENERAL = "general"
        const val CHANNEL_DOWNLOADS = "downloads"
        const val CHANNEL_MESSAGES = "messages"
        const val CHANNEL_FOREGROUND_SERVICE = "foreground_service"
    }

    fun createAllChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channels = listOf(
                NotificationChannel(
                    CHANNEL_GENERAL,
                    "General Notifications",
                    NotificationManager.IMPORTANCE_DEFAULT
                ).apply {
                    description = "General app notifications"
                },
                
                NotificationChannel(
                    CHANNEL_DOWNLOADS,
                    "Downloads",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "Download progress notifications"
                    setShowBadge(false)
                },
                
                NotificationChannel(
                    CHANNEL_MESSAGES,
                    "Messages",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "New message notifications"
                    enableVibration(true)
                    enableLights(true)
                },
                
                NotificationChannel(
                    CHANNEL_FOREGROUND_SERVICE,
                    "Background Tasks",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "Ongoing background operations"
                    setShowBadge(false)
                }
            )

            val notificationManager = NotificationManagerCompat.from(context)
            channels.forEach { channel ->
                notificationManager.createNotificationChannel(channel)
            }
        }
    }
}
```

### Initialize in Application

```kotlin
// app/MyApplication.kt
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var notificationChannels: NotificationChannels
    
    override fun onCreate() {
        super.onCreate()
        notificationChannels.createAllChannels()
    }
}
```

## Basic Notifications

### Simple Notification

```kotlin
import android.Manifest
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.example.core.notifications.NotificationChannels
import javax.inject.Inject

class NotificationHelper @Inject constructor(
    private val context: Context
) {
    fun showSimpleNotification(
        title: String,
        message: String,
        notificationId: Int = System.currentTimeMillis().toInt()
    ) {
        // Check permission for API 33+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val permissionGranted = context.checkSelfPermission(
                Manifest.permission.POST_NOTIFICATIONS
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED
            
            if (!permissionGranted) return
        }

        val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_GENERAL)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(context).notify(notificationId, notification)
    }
}
```

### Notification with Tap Action

Use `PendingIntent` to open a specific screen:

```kotlin
fun showNotificationWithAction(
    title: String,
    message: String,
    targetRoute: String,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    // Check permission for API 33+
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    // Deep link to specific screen
    val intent = Intent(
        Intent.ACTION_VIEW,
        "app://example.com/$targetRoute".toUri(),
        context,
        MainActivity::class.java
    ).apply {
        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
    }

    val pendingIntent = PendingIntent.getActivity(
        context,
        notificationId,
        intent,
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_GENERAL)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(message)
        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        .setContentIntent(pendingIntent)
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

## Notification Styles

### BigTextStyle

For long text content:

```kotlin
fun showBigTextNotification(
    title: String,
    shortText: String,
    longText: String,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_GENERAL)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(shortText) // Shown when collapsed
        .setStyle(
            NotificationCompat.BigTextStyle()
                .bigText(longText) // Shown when expanded
                .setBigContentTitle(title)
        )
        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

### BigPictureStyle

For image notifications:

```kotlin
fun showBigPictureNotification(
    title: String,
    text: String,
    bitmap: Bitmap,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_GENERAL)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(text)
        .setLargeIcon(bitmap) // Shown when collapsed
        .setStyle(
            NotificationCompat.BigPictureStyle()
                .bigPicture(bitmap) // Shown when expanded
                .setBigContentTitle(title)
                .setSummaryText(text)
        )
        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

### InboxStyle

For multiple lines of information:

```kotlin
fun showInboxStyleNotification(
    title: String,
    lines: List<String>,
    summaryText: String? = null,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val inboxStyle = NotificationCompat.InboxStyle()
    lines.forEach { line ->
        inboxStyle.addLine(line)
    }
    
    summaryText?.let { inboxStyle.setSummaryText(it) }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_MESSAGES)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText("${lines.size} new messages")
        .setStyle(inboxStyle)
        .setPriority(NotificationCompat.PRIORITY_HIGH)
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

### MessagingStyle

For conversations (API 24+):

```kotlin
fun showMessagingStyleNotification(
    conversationTitle: String,
    messages: List<Message>,
    currentUser: Person,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val messagingStyle = NotificationCompat.MessagingStyle(currentUser)
        .setConversationTitle(conversationTitle)

    messages.forEach { message ->
        messagingStyle.addMessage(
            NotificationCompat.MessagingStyle.Message(
                message.text,
                message.timestamp,
                message.sender
            )
        )
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_MESSAGES)
        .setSmallIcon(R.drawable.ic_notification)
        .setStyle(messagingStyle)
        .setPriority(NotificationCompat.PRIORITY_HIGH)
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}

data class Message(
    val text: String,
    val timestamp: Long,
    val sender: Person
)
```

## Action Buttons

### Basic Actions

```kotlin
fun showNotificationWithActions(
    title: String,
    message: String,
    notificationId: Int = System.currentTimeMillis().toInt()
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    // Create PendingIntents for actions
    val acceptIntent = createBroadcastIntent(ACTION_ACCEPT, notificationId)
    val declineIntent = createBroadcastIntent(ACTION_DECLINE, notificationId)

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_GENERAL)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(message)
        .setPriority(NotificationCompat.PRIORITY_HIGH)
        .addAction(
            R.drawable.ic_check,
            "Accept",
            acceptIntent
        )
        .addAction(
            R.drawable.ic_close,
            "Decline",
            declineIntent
        )
        .setAutoCancel(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}

private fun createBroadcastIntent(action: String, notificationId: Int): PendingIntent {
    val intent = Intent(context, NotificationActionReceiver::class.java).apply {
        this.action = action
        putExtra(EXTRA_NOTIFICATION_ID, notificationId)
    }
    
    return PendingIntent.getBroadcast(
        context,
        notificationId,
        intent,
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )
}

companion object {
    const val ACTION_ACCEPT = "com.example.ACTION_ACCEPT"
    const val ACTION_DECLINE = "com.example.ACTION_DECLINE"
    const val EXTRA_NOTIFICATION_ID = "notification_id"
}
```

### Notification Action Receiver

Handle notification actions in a BroadcastReceiver:

```kotlin
// core/notifications/NotificationActionReceiver.kt
@AndroidEntryPoint
class NotificationActionReceiver : BroadcastReceiver() {
    @Inject lateinit var notificationRepository: NotificationRepository

    override fun onReceive(context: Context, intent: Intent) {
        val notificationId = intent.getIntExtra(
            NotificationHelper.EXTRA_NOTIFICATION_ID,
            -1
        )

        when (intent.action) {
            NotificationHelper.ACTION_ACCEPT -> {
                // Handle accept action
                notificationRepository.handleAccept(notificationId)
                dismissNotification(context, notificationId)
            }
            NotificationHelper.ACTION_DECLINE -> {
                // Handle decline action
                notificationRepository.handleDecline(notificationId)
                dismissNotification(context, notificationId)
            }
        }
    }

    private fun dismissNotification(context: Context, notificationId: Int) {
        NotificationManagerCompat.from(context).cancel(notificationId)
    }
}
```

Register in AndroidManifest.xml:

```xml
<receiver
    android:name=".core.notifications.NotificationActionReceiver"
    android:exported="false">
    <intent-filter>
        <action android:name="com.example.ACTION_ACCEPT" />
        <action android:name="com.example.ACTION_DECLINE" />
    </intent-filter>
</receiver>
```

## Progress Notifications

### Determinate Progress

```kotlin
fun showProgressNotification(
    title: String,
    progress: Int,
    maxProgress: Int = 100,
    notificationId: Int
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_DOWNLOADS)
        .setSmallIcon(R.drawable.ic_download)
        .setContentTitle(title)
        .setContentText("Downloading...")
        .setProgress(maxProgress, progress, false)
        .setOngoing(true) // Prevent dismissal while in progress
        .setPriority(NotificationCompat.PRIORITY_LOW)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}

fun showDownloadCompleteNotification(
    title: String,
    notificationId: Int
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_DOWNLOADS)
        .setSmallIcon(R.drawable.ic_check)
        .setContentTitle(title)
        .setContentText("Download complete")
        .setProgress(0, 0, false) // Remove progress bar
        .setOngoing(false)
        .setAutoCancel(true)
        .setPriority(NotificationCompat.PRIORITY_LOW)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

### Indeterminate Progress

```kotlin
fun showIndeterminateProgressNotification(
    title: String,
    message: String,
    notificationId: Int
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val permissionGranted = context.checkSelfPermission(
            Manifest.permission.POST_NOTIFICATIONS
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        
        if (!permissionGranted) return
    }

    val notification = NotificationCompat.Builder(context, NotificationChannels.CHANNEL_DOWNLOADS)
        .setSmallIcon(R.drawable.ic_sync)
        .setContentTitle(title)
        .setContentText(message)
        .setProgress(0, 0, true) // Indeterminate
        .setOngoing(true)
        .setPriority(NotificationCompat.PRIORITY_LOW)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

## Progress-Centric Notifications (API 36+)

Android 16 introduces `Notification.ProgressStyle`, a rich notification style for tracking user-initiated journeys from start to end. Use this for rideshare, delivery, navigation, and any multi-step process.

### ProgressStyle Notification

```kotlin
fun showProgressStyleNotification(
    title: String,
    currentSegmentText: String,
    notificationId: Int
) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.BAKLAVA) {
        showProgressNotification(title, 50, notificationId = notificationId)
        return
    }

    val progressStyle = Notification.ProgressStyle().apply {
        addSegment(Notification.ProgressStyle.Segment(500).apply {
            color = android.graphics.Color.GREEN
        })
        addSegment(Notification.ProgressStyle.Segment(1000))
        addPoint(Notification.ProgressStyle.Point(750).apply {
            color = android.graphics.Color.RED
        })
        progress = 250
        progressTrackerIcon = Icon.createWithResource(context, R.drawable.ic_car)
    }

    val notification = Notification.Builder(context, NotificationChannels.CHANNEL_GENERAL)
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle(title)
        .setContentText(currentSegmentText)
        .setStyle(progressStyle)
        .setOngoing(true)
        .build()

    NotificationManagerCompat.from(context).notify(notificationId, notification)
}
```

**Key concepts:**
- **Segments**: Divide the journey into phases with optional colors
- **Points**: Mark milestones along the journey (e.g., pickup, dropoff)
- **Progress**: Current position along the total journey
- **Tracker icon**: Visual indicator of the current position

**When to use ProgressStyle vs standard progress:**
- Use `ProgressStyle` for multi-step user journeys (rideshare, delivery, navigation)
- Use standard `setProgress()` for simple determinate/indeterminate tasks (downloads, uploads)
- `ProgressStyle` is only available on API 36+; provide a fallback for older APIs

## Foreground Service Notifications

Foreground services **require** a notification on all API levels.

### Foreground Service Setup

```kotlin
// core/sync/SyncWorker.kt
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val syncRepository: SyncRepository
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        setForeground(createForegroundInfo())
        
        try {
            syncRepository.sync()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun createForegroundInfo(): ForegroundInfo {
        val notification = NotificationCompat.Builder(
            applicationContext,
            NotificationChannels.CHANNEL_FOREGROUND_SERVICE
        )
            .setSmallIcon(R.drawable.ic_sync)
            .setContentTitle("Syncing data")
            .setContentText("Synchronizing your data in the background...")
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
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
        private const val NOTIFICATION_ID = 1001
    }
}
```

### Foreground Service in Android Service

For long-running operations:

```kotlin
// core/sync/SyncForegroundService.kt
@AndroidEntryPoint
class SyncForegroundService : Service() {
    @Inject lateinit var syncRepository: SyncRepository
    
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        
        // Start foreground BEFORE doing work
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        scope.launch {
            try {
                syncRepository.sync()
            } finally {
                stopSelf()
            }
        }

        return START_NOT_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(
            this,
            NotificationChannels.CHANNEL_FOREGROUND_SERVICE
        )
            .setSmallIcon(R.drawable.ic_sync)
            .setContentTitle("Syncing data")
            .setContentText("Synchronizing your data...")
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    companion object {
        private const val NOTIFICATION_ID = 1001
    }
}
```

Declare in AndroidManifest.xml:

```xml
<!-- API 28+ requires foreground service permission -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />

<application>
    <service
        android:name=".core.sync.SyncForegroundService"
        android:foregroundServiceType="dataSync"
        android:exported="false" />
</application>
```

## Notification Manager Interface

Follow our architecture patterns with testable interfaces:

```kotlin
// core/notifications/NotificationManager.kt
package com.example.core.notifications

interface NotificationManager {
    fun showNotification(
        title: String,
        message: String,
        notificationId: Int = generateId()
    )
    
    fun showNotificationWithAction(
        title: String,
        message: String,
        targetRoute: String,
        notificationId: Int = generateId()
    )
    
    fun showProgressNotification(
        title: String,
        progress: Int,
        maxProgress: Int = 100,
        notificationId: Int
    )
    
    fun dismissNotification(notificationId: Int)
    
    fun dismissAllNotifications()
    
    companion object {
        fun generateId(): Int = System.currentTimeMillis().toInt()
    }
}
```

### Implementation

```kotlin
// core/notifications/AndroidNotificationManager.kt
@Singleton
class AndroidNotificationManager @Inject constructor(
    @ApplicationContext private val context: Context
) : NotificationManager {
    
    private val notificationManagerCompat = NotificationManagerCompat.from(context)

    override fun showNotification(
        title: String,
        message: String,
        notificationId: Int
    ) {
        if (!hasNotificationPermission()) return

        val notification = NotificationCompat.Builder(
            context,
            NotificationChannels.CHANNEL_GENERAL
        )
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        notificationManagerCompat.notify(notificationId, notification)
    }

    override fun showNotificationWithAction(
        title: String,
        message: String,
        targetRoute: String,
        notificationId: Int
    ) {
        if (!hasNotificationPermission()) return

        val intent = Intent(
            Intent.ACTION_VIEW,
            "app://example.com/$targetRoute".toUri(),
            context,
            MainActivity::class.java
        ).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            notificationId,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(
            context,
            NotificationChannels.CHANNEL_GENERAL
        )
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        notificationManagerCompat.notify(notificationId, notification)
    }

    override fun showProgressNotification(
        title: String,
        progress: Int,
        maxProgress: Int,
        notificationId: Int
    ) {
        if (!hasNotificationPermission()) return

        val notification = NotificationCompat.Builder(
            context,
            NotificationChannels.CHANNEL_DOWNLOADS
        )
            .setSmallIcon(R.drawable.ic_download)
            .setContentTitle(title)
            .setContentText("Downloading...")
            .setProgress(maxProgress, progress, false)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        notificationManagerCompat.notify(notificationId, notification)
    }

    override fun dismissNotification(notificationId: Int) {
        notificationManagerCompat.cancel(notificationId)
    }

    override fun dismissAllNotifications() {
        notificationManagerCompat.cancelAll()
    }

    private fun hasNotificationPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED
        } else {
            true // No permission required on API < 33
        }
    }
}
```

### Hilt Module

```kotlin
// core/di/NotificationModule.kt
@Module
@InstallIn(SingletonComponent::class)
abstract class NotificationModule {
    @Binds
    abstract fun bindNotificationManager(
        impl: AndroidNotificationManager
    ): NotificationManager
}
```

## Architecture Integration

### Repository Layer

```kotlin
// feature/messages/data/MessageRepository.kt
interface MessageRepository {
    suspend fun sendMessage(text: String): Result<Message>
    fun observeNewMessages(): Flow<Message>
}

class MessageRepositoryImpl @Inject constructor(
    private val messageApi: MessageApi,
    private val notificationManager: NotificationManager
) : MessageRepository {

    override suspend fun sendMessage(text: String): Result<Message> = runCatching {
        messageApi.sendMessage(text)
    }

    override fun observeNewMessages(): Flow<Message> = flow {
        // Observe new messages from remote source
        messageApi.observeMessages().collect { message ->
            // Show notification for new messages
            notificationManager.showNotificationWithAction(
                title = message.senderName,
                message = message.text,
                targetRoute = "messages/${message.id}"
            )
            emit(message)
        }
    }
}
```

### ViewModel Layer

```kotlin
// feature/sync/presentation/SyncViewModel.kt
@HiltViewModel
class SyncViewModel @Inject constructor(
    private val syncRepository: SyncRepository,
    private val notificationManager: NotificationManager
) : ViewModel() {

    private val notificationId = NotificationManager.generateId()

    fun startSync() {
        viewModelScope.launch {
            syncRepository.sync()
                .onStart {
                    notificationManager.showProgressNotification(
                        title = "Syncing",
                        progress = 0,
                        notificationId = notificationId
                    )
                }
                .collect { progress ->
                    notificationManager.showProgressNotification(
                        title = "Syncing",
                        progress = progress,
                        notificationId = notificationId
                    )
                }
        }
    }
}
```

## Testing

### Fake NotificationManager

```kotlin
// core/notifications/testing/FakeNotificationManager.kt
class FakeNotificationManager : NotificationManager {
    private val _notifications = mutableListOf<NotificationData>()
    val notifications: List<NotificationData> = _notifications

    override fun showNotification(
        title: String,
        message: String,
        notificationId: Int
    ) {
        _notifications.add(
            NotificationData(
                id = notificationId,
                title = title,
                message = message
            )
        )
    }

    override fun showNotificationWithAction(
        title: String,
        message: String,
        targetRoute: String,
        notificationId: Int
    ) {
        _notifications.add(
            NotificationData(
                id = notificationId,
                title = title,
                message = message,
                targetRoute = targetRoute
            )
        )
    }

    override fun showProgressNotification(
        title: String,
        progress: Int,
        maxProgress: Int,
        notificationId: Int
    ) {
        val existing = _notifications.find { it.id == notificationId }
        if (existing != null) {
            _notifications.remove(existing)
        }
        
        _notifications.add(
            NotificationData(
                id = notificationId,
                title = title,
                progress = progress,
                maxProgress = maxProgress
            )
        )
    }

    override fun dismissNotification(notificationId: Int) {
        _notifications.removeAll { it.id == notificationId }
    }

    override fun dismissAllNotifications() {
        _notifications.clear()
    }

    fun assertNotificationShown(title: String) {
        assert(_notifications.any { it.title == title })
    }

    fun assertNotificationCount(expected: Int) {
        assert(_notifications.size == expected)
    }
}

data class NotificationData(
    val id: Int,
    val title: String,
    val message: String? = null,
    val targetRoute: String? = null,
    val progress: Int? = null,
    val maxProgress: Int? = null
)
```

### Testing Repository

```kotlin
// feature/messages/data/MessageRepositoryTest.kt
@Test
fun `observeNewMessages shows notification for each message`() = runTest {
    val fakeNotificationManager = FakeNotificationManager()
    val repository = MessageRepositoryImpl(
        messageApi = fakeMessageApi,
        notificationManager = fakeNotificationManager
    )

    repository.observeNewMessages().take(2).collect()

    fakeNotificationManager.assertNotificationCount(2)
    fakeNotificationManager.assertNotificationShown("John Doe")
}
```

### Testing ViewModel

```kotlin
// feature/sync/presentation/SyncViewModelTest.kt
@Test
fun `startSync shows progress notification`() = runTest {
    val fakeNotificationManager = FakeNotificationManager()
    val viewModel = SyncViewModel(
        syncRepository = fakeSyncRepository,
        notificationManager = fakeNotificationManager
    )

    viewModel.startSync()
    advanceUntilIdle()

    fakeNotificationManager.assertNotificationShown("Syncing")
}
```

## Best Practices

### ✅ Always Do

1. **Create notification channels** at app startup (no-op on API < 26)
2. **Check POST_NOTIFICATIONS permission** on API 33+ before showing notifications
3. **Use NotificationCompat** for backward compatibility
4. **Use FLAG_IMMUTABLE** for PendingIntents on API 23+
5. **Set unique notification IDs** to avoid overwriting notifications
6. **Use foreground notifications** for long-running operations
7. **Provide meaningful icons** for small icon, large icon, and action buttons
8. **Test notifications** on multiple API levels (24, 26, 29, 31, 33, 36)
9. **Use interfaces** for testability in repositories/ViewModels
10. **Handle notification permission** gracefully (don't crash if denied)

### ❌ Never Do

1. **Never show notifications without permission check** on API 33+
2. **Never use FLAG_MUTABLE** for PendingIntents unless absolutely necessary (security risk)
3. **Never hardcode notification IDs** (use unique IDs or timestamp-based IDs)
4. **Never forget to call startForeground()** within 5 seconds of starting a foreground service
5. **Never use setOngoing(true)** for dismissible notifications
6. **Never rely on notifications** for critical user-facing information (they can be disabled)
7. **Never create channels dynamically** for every notification (create once at startup)
8. **Never show notifications from background** on API 26+ without proper foreground service

### Notification ID Strategy

```kotlin
object NotificationIds {
    // Fixed IDs for single-instance notifications
    const val SYNC_SERVICE = 1001
    const val DOWNLOAD_SERVICE = 1002
    
    // Dynamic IDs for multiple notifications
    fun forMessage(messageId: String): Int = messageId.hashCode()
    fun forDownload(downloadId: String): Int = "download_$downloadId".hashCode()
}
```

### Channel Importance Levels

- `IMPORTANCE_HIGH`: Time-sensitive (messages, calls) - shows heads-up notification
- `IMPORTANCE_DEFAULT`: Standard notifications
- `IMPORTANCE_LOW`: Background operations (downloads, sync) - no sound
- `IMPORTANCE_MIN`: For ongoing foreground services - no sound, no badge

### PendingIntent Flags

For API 23+, always use:
```kotlin
PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
```

For mutable PendingIntents (API 31+):
```kotlin
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
    PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
} else {
    PendingIntent.FLAG_UPDATE_CURRENT
}
```

## References

- [Android Notifications Guide](https://developer.android.com/develop/ui/views/notifications)
- [NotificationCompat API](https://developer.android.com/reference/androidx/core/app/NotificationCompat)
- [Notification Channels](https://developer.android.com/develop/ui/views/notifications/channels)
- [Foreground Services](https://developer.android.com/develop/background-work/services/foreground-services)
- [Material Design Notifications](https://m3.material.io/foundations/interaction/notifications/overview)
- [POST_NOTIFICATIONS Permission](https://developer.android.com/develop/ui/views/notifications/notification-permission)
