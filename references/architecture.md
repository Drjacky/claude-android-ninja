# Architecture Guide

Based on Google's official Android architecture guidance with modern Jetpack Compose, Navigation3, and modular best practices.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Architecture Principles](#architecture-principles)
3. [Module Structure](#module-structure)
4. [Data Layer](#data-layer)
5. [Domain Layer](#domain-layer)
6. [Presentation Layer](#presentation-layer)
7. [UI Layer](#ui-layer)
8. [Navigation](#navigation)
9. [Complete Architecture Flow](#complete-architecture-flow)

## Architecture Overview

Four-layer architecture with strict module separation and unidirectional data flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FEATURE MODULES (feature/*)                        │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              Presentation Layer                                 │   │
│   │  ┌──────────────┐    ┌──────────────────────────┐               │   │
│   │  │   Screen     │◄───│      ViewModel           │               │   │
│   │  │  (Compose)   │    │  (StateFlow<UiState>)    │               │   │
│   │  └──────────────┘    └────────────┬─────────────┘               │   │
│   │                                   │                             │   │
│   └───────────────────────────────────┼─────────────────────────────┘   │
│                                       │ Uses                            │
├───────────────────────────────────────┼─────────────────────────────────┤
│              CORE/DOMAIN Module       │                                 │
│   ┌───────────────────────────────────▼──────────────────────┐          │
│   │                    Domain Layer                          │          │
│   │  ┌────────────────────────────────────────────────────┐  │          │
│   │  │                Use Cases                           │  │          │
│   │  │           (combine/transform logic)                │  │          │
│   │  └───────────────────────┬────────────────────────────┘  │          │
│   │  ┌───────────────────────▼────────────────────────────┐  │          │
│   │  │             Repository Interfaces                  │  │          │
│   │  │           (contracts for data layer)               │  │          │
│   │  └───────────────────────┬────────────────────────────┘  │          │
│   │  ┌───────────────────────▼────────────────────────────┐  │          │
│   │  │                Domain Models                       │  │          │
│   │  │           (business entities)                      │  │          │
│   │  └────────────────────────────────────────────────────┘  │          │
│   └────────────────────────────────────┬─────────────────────┘          │
│                                        │ Implements                     │
├────────────────────────────────────────┼────────────────────────────────┤
│                CORE/DATA Module        │                                │
│   ┌────────────────────────────────────▼──────────────────────┐         │
│   │                    Data Layer                             │         │
│   │  ┌────────────────────────────────────────────────────┐   │         │
│   │  │              Repository Implementations            │   │         │
│   │  │    (offline-first, single source of truth)         │   │         │
│   │  └─────────┬─────────────────────┬────────────────────┘   │         │
│   │            │                     │                        │         │
│   │  ┌─────────▼─────────┐  ┌────────▼──────────────┐         │         │
│   │  │  Local DataSource │  │  Remote DataSource    │         │         │
│   │  │   (Room + DAO)    │  │     (Retrofit)        │         │         │
│   │  └─────────┬─────────┘  └───────────────────────┘         │         │
│   │            │                                              │         │
│   │  ┌─────────▼──────────────────────────────────────┐       │         │
│   │  │              Data Models                       │       │         │
│   │  │      (Entity, DTO, Response objects)           │       │         │
│   │  └────────────────────────────────────────────────┘       │         │
│   └───────────────────────────────────────────────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                 CORE/UI Module (shared UI resources)                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    UI Layer                                     │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │        Shared UI Components                             │    │   │
│   │  │   (Buttons, Cards, Dialogs, etc.)                       │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │           Themes & Design System                        │    │   │
│   │  │   (Colors, Typography, Shapes)                          │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │         Base ViewModels / State Management              │    │   │
│   │  │   (BaseViewModel, UiState, etc.)                        │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Architecture Principles

1. **Offline-first**: Local database is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use Kotlin Flow/StateFlow for all data exposure
4. **Modular by feature**: Each feature is self-contained with clear boundaries
5. **Testable by design**: Use interfaces and test doubles, no mocking libraries
6. **Layer separation**: Strict separation between Presentation, Domain, Data, and UI layers
7. **Dependency direction**: Features depend on Core modules, not on other features
8. **Navigation coordination**: App module coordinates navigation between features

## Module Structure

```
app/                    # App module - navigation, DI setup, app entry point
feature/
  ├── feature-auth/     # Authentication feature
  ├── feature-home/     # Home screen feature
  ├── feature-profile/  # User profile feature
  ├── feature-settings/ # App settings feature
  └── feature-<name>/   # Additional features...
core/
  ├── domain/           # Pure Kotlin: Use Cases, Repository interfaces, Domain models
  ├── data/             # Data layer: Repository impl, DataSources, Data models
  ├── ui/               # Shared UI components, themes, base ViewModels
  ├── network/          # Retrofit, API models, network utilities
  ├── database/         # Room DAOs, entities, migrations
  ├── datastore/        # Preferences storage
  ├── common/           # Shared utilities, extensions
  └── testing/          # Test utilities, test doubles
```

## Data Layer

### Principles
- **Offline-first**: Local database is the source of truth
- **Repository pattern**: Single public API for data access
- **Reactive streams**: All data exposed as `Flow<T>` or `StateFlow<T>`
- **Model mapping**: Separate Entity (database), DTO (network), and Domain models

### Repository Pattern

```kotlin
// core/domain - Repository interface (contract)
interface TopicsRepository {
    fun getTopics(): Flow<List<Topic>>
    fun getTopic(id: String): Flow<Topic>
    suspend fun syncWith(synchronizer: Synchronizer): Boolean
    suspend fun refreshTopics(): Result<Unit>
}

// core/data - Repository implementation
internal class OfflineFirstTopicsRepository @Inject constructor(
    private val topicDao: TopicDao,
    private val networkDataSource: NetworkDataSource,
    private val topicMapper: TopicMapper
) : TopicsRepository {

    override fun getTopics(): Flow<List<Topic>> =
        topicDao.getTopicEntities()
            .map { entities -> entities.map(topicMapper::toDomain) }
            .catch { e -> emit(emptyList()) } // Graceful error handling

    override fun getTopic(id: String): Flow<Topic> =
        topicDao.getTopicEntity(id)
            .map(topicMapper::toDomain)

    override suspend fun syncWith(synchronizer: Synchronizer): Boolean =
        synchronizer.changeListSync(
            versionReader = ChangeListVersions::topicVersion,
            changeListFetcher = { networkDataSource.getTopicChangeList(after = it) },
            versionUpdater = { latestVersion ->
                copy(topicVersion = latestVersion)
            },
            modelDeleter = topicDao::deleteTopics,
            modelUpdater = { changedIds ->
                val networkTopics = networkDataSource.getTopics(ids = changedIds)
                topicDao.upsertTopics(networkTopics.map(topicMapper::toEntity))
            },
        )

    override suspend fun refreshTopics(): Result<Unit> = runCatching {
        val topics = networkDataSource.getTopics()
        topicDao.upsertTopics(topics.map(topicMapper::toEntity))
    }
}
```

### Data Sources

| Type        | Module         | Implementation  | Purpose                             |
|-------------|----------------|-----------------|-------------------------------------|
| Local       | core/database  | Room DAO        | Persistent storage, source of truth |
| Remote      | core/network   | Retrofit API    | Network data fetching               |
| Preferences | core/datastore | Proto DataStore | User settings, simple key-value     |

### Model Mapping Strategy

```kotlin
// core/data/mapping/TopicMapper.kt
class TopicMapper @Inject constructor() {
    
    // Entity → Domain
    fun toDomain(entity: TopicEntity): Topic = Topic(
        id = entity.id,
        name = entity.name,
        description = entity.description,
        imageUrl = entity.imageUrl,
        createdAt = entity.createdAt,
        updatedAt = entity.updatedAt
    )
    
    // DTO → Entity
    fun toEntity(dto: TopicDto): TopicEntity = TopicEntity(
        id = dto.id,
        name = dto.name,
        description = dto.description,
        imageUrl = dto.imageUrl,
        createdAt = Instant.parse(dto.createdAt),
        updatedAt = Instant.parse(dto.updatedAt)
    )
    
    // Domain → Entity (optional, for updates)
    fun toEntity(domain: Topic): TopicEntity = TopicEntity(
        id = domain.id,
        name = domain.name,
        description = domain.description,
        imageUrl = domain.imageUrl,
        createdAt = domain.createdAt,
        updatedAt = domain.updatedAt
    )
}
```

### Data Synchronization

```kotlin
// core/data/sync/SyncWorker.kt
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val newsRepository: NewsRepository,
    private val topicsRepository: TopicsRepository,
) : CoroutineWorker(context, params), Synchronizer {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val results = listOf(
                newsRepository.syncWith(this@SyncWorker),
                topicsRepository.syncWith(this@SyncWorker),
            )
            
            if (results.all { it }) {
                Result.success()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Result.failure()
        }
    }
}
```

## Domain Layer

### Purpose
- **Pure Kotlin module** (no Android dependencies)
- Encapsulate complex business logic
- Remove duplicate logic from ViewModels
- Combine and transform data from multiple repositories
- **Optional but recommended** for complex applications

### Use Case Pattern

```kotlin
// core/domain/usecase/GetUserNewsResourcesUseCase.kt
class GetUserNewsResourcesUseCase @Inject constructor(
    private val newsRepository: NewsRepository,
    private val userDataRepository: UserDataRepository,
    private val newsMapper: NewsMapper
) {
    operator fun invoke(): Flow<List<UserNewsResource>> =
        newsRepository.getNewsResources()
            .combine(userDataRepository.userData) { newsResources, userData ->
                newsResources.map { news ->
                    newsMapper.toUserNewsResource(news, userData)
                }
            }
            .map { resources ->
                resources.sortedByDescending { it.publishedAt }
            }
}

// core/domain/usecase/BookmarkNewsUseCase.kt
class BookmarkNewsUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository
) {
    suspend operator fun invoke(newsResourceId: String, bookmarked: Boolean): Result<Unit> =
        runCatching {
            userDataRepository.setNewsResourceBookmarked(newsResourceId, bookmarked)
        }
}
```

### Repository Interface Pattern

```kotlin
// core/domain/repository/NewsRepository.kt
interface NewsRepository {
    fun getNewsResources(): Flow<List<NewsResource>>
    fun getNewsResource(id: String): Flow<NewsResource>
    suspend fun refreshNewsResources(): Result<Unit>
    suspend fun syncWith(synchronizer: Synchronizer): Boolean
    
    // Events
    fun observeNewsEvents(): Flow<NewsEvent>
}
```

### Domain Models

```kotlin
// core/domain/model/
data class Topic(
    val id: String,
    val name: String,
    val description: String,
    val imageUrl: String?,
    val createdAt: Instant,
    val updatedAt: Instant
)

data class UserNewsResource(
    val id: String,
    val title: String,
    val content: String,
    val url: String,
    val publishedAt: Instant,
    val topics: List<Topic>,
    val isBookmarked: Boolean,
    val isFollowing: Boolean
)

sealed class NewsEvent {
    data class ResourceUpdated(val id: String) : NewsEvent()
    data class SyncCompleted(val timestamp: Instant) : NewsEvent()
    data class Error(val message: String, val retryable: Boolean) : NewsEvent()
}
```

## Presentation Layer

### Location: Feature modules (`feature/*`)

### Components
- **Screen**: Main composable UI
- **ViewModel**: State holder and event processor
- **UiState**: Sealed interface representing all possible UI states
- **Actions**: Sealed class representing user interactions

### UiState Modeling

```kotlin
// feature-home/presentation/viewmodel/HomeUiState.kt
sealed interface HomeUiState {
    data object Loading : HomeUiState
    
    data class Success(
        val feed: List<UserNewsResource>,
        val selectedTopic: String? = null,
        val isRefreshing: Boolean = false,
        val isLoadingMore: Boolean = false
    ) : HomeUiState
    
    data class Error(
        val message: String,
        val canRetry: Boolean = true,
        val errorType: ErrorType = ErrorType.Network
    ) : HomeUiState
    
    data object Empty : HomeUiState
}

enum class ErrorType {
    Network, Server, Database, Unknown
}
```

### Actions Pattern

```kotlin
// feature-home/presentation/viewmodel/HomeActions.kt
sealed class HomeAction {
    // Data loading
    data object LoadInitial : HomeAction()
    data object Refresh : HomeAction()
    data object LoadMore : HomeAction()
    
    // User interactions
    data class SelectTopic(val topicId: String) : HomeAction()
    data class ToggleBookmark(val resourceId: String) : HomeAction()
    data class NavigateToDetail(val resourceId: String) : HomeAction()
    
    // Error handling
    data object Retry : HomeAction()
    data object ClearError : HomeAction()
    
    // Navigation
    data object NavigateToSettings : HomeAction()
    data object NavigateToProfile : HomeAction()
}
```

### ViewModel Pattern

```kotlin
// feature-home/presentation/viewmodel/HomeViewModel.kt
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getUserNewsResourcesUseCase: GetUserNewsResourcesUseCase,
    private val bookmarkNewsUseCase: BookmarkNewsUseCase,
    private val topicsRepository: TopicsRepository,
    private val appDispatchers: AppDispatchers
) : ViewModel() {

    private val _uiState = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()
    
    private val _actions = MutableSharedFlow<HomeAction>()
    val actions: SharedFlow<HomeAction> = _actions.asSharedFlow()
    
    init {
        loadInitialData()
        observeDataChanges()
    }
    
    fun onAction(action: HomeAction) {
        viewModelScope.launch(appDispatchers.io) {
            when (action) {
                HomeAction.LoadInitial -> loadInitialData()
                HomeAction.Refresh -> refreshData()
                HomeAction.LoadMore -> loadMoreData()
                is HomeAction.SelectTopic -> selectTopic(action.topicId)
                is HomeAction.ToggleBookmark -> toggleBookmark(action.resourceId)
                is HomeAction.NavigateToDetail -> navigateToDetail(action.resourceId)
                HomeAction.Retry -> handleRetry()
                HomeAction.ClearError -> clearError()
                HomeAction.NavigateToSettings -> navigateToSettings()
                HomeAction.NavigateToProfile -> navigateToProfile()
            }
        }
    }
    
    private fun loadInitialData() {
        viewModelScope.launch {
            _uiState.value = HomeUiState.Loading
            
            getUserNewsResourcesUseCase()
                .catch { e ->
                    _uiState.value = HomeUiState.Error(
                        message = "Failed to load data: ${e.message}",
                        canRetry = true
                    )
                }
                .collect { newsResources ->
                    _uiState.value = if (newsResources.isEmpty()) {
                        HomeUiState.Empty
                    } else {
                        HomeUiState.Success(feed = newsResources)
                    }
                }
        }
    }
    
    private suspend fun toggleBookmark(resourceId: String) {
        val currentState = _uiState.value
        if (currentState is HomeUiState.Success) {
            val currentFeed = currentState.feed.toMutableList()
            val index = currentFeed.indexOfFirst { it.id == resourceId }
            
            if (index != -1) {
                val resource = currentFeed[index]
                val updatedResource = resource.copy(isBookmarked = !resource.isBookmarked)
                currentFeed[index] = updatedResource
                
                // Optimistic update
                _uiState.value = currentState.copy(feed = currentFeed)
                
                // Actual update
                bookmarkNewsUseCase(resourceId, updatedResource.isBookmarked)
                    .onFailure { e ->
                        // Revert on failure
                        currentFeed[index] = resource
                        _uiState.value = currentState.copy(feed = currentFeed)
                    }
            }
        }
    }
    
    private fun observeDataChanges() {
        viewModelScope.launch {
            topicsRepository.observeNewsEvents()
                .collect { event ->
                    when (event) {
                        is NewsEvent.SyncCompleted -> {
                            if (_uiState.value is HomeUiState.Success) {
                                loadInitialData() // Refresh on sync completion
                            }
                        }
                        is NewsEvent.Error -> {
                            // Handle error events
                        }
                        else -> Unit
                    }
                }
        }
    }
}
```

## UI Layer

### Location: `core/ui` (shared) and feature modules (specific)

### Screen Composition Pattern

```kotlin
// feature-home/presentation/HomeScreen.kt
@Composable
fun HomeScreen(
    onNavigateToDetail: (String) -> Unit,
    onNavigateToSettings: () -> Unit,
    onNavigateToProfile: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val coroutineScope = rememberCoroutineScope()
    
    // Handle navigation actions
    LaunchedEffect(Unit) {
        viewModel.actions.collect { action ->
            when (action) {
                is HomeAction.NavigateToDetail -> onNavigateToDetail(action.resourceId)
                HomeAction.NavigateToSettings -> onNavigateToSettings()
                HomeAction.NavigateToProfile -> onNavigateToProfile()
                else -> Unit
            }
        }
    }
    
    HomeContent(
        uiState = uiState,
        onAction = { action ->
            coroutineScope.launch {
                viewModel.onAction(action)
            }
        },
        modifier = Modifier.fillMaxSize()
    )
}

@Composable
private fun HomeContent(
    uiState: HomeUiState,
    onAction: (HomeAction) -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier) {
        when (uiState) {
            HomeUiState.Loading -> LoadingScreen()
            is HomeUiState.Success -> SuccessContent(uiState, onAction)
            is HomeUiState.Error -> ErrorContent(uiState, onAction)
            HomeUiState.Empty -> EmptyStateScreen(onAction)
        }
    }
}

@Composable
private fun SuccessContent(
    uiState: HomeUiState.Success,
    onAction: (HomeAction) -> Unit
) {
    Scaffold(
        topBar = {
            HomeTopBar(
                onSettingsClick = { onAction(HomeAction.NavigateToSettings) },
                onProfileClick = { onAction(HomeAction.NavigateToProfile) }
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { onAction(HomeAction.Refresh) },
                icon = { Icon(Icons.Default.Refresh, "Refresh") },
                text = { Text("Refresh") },
                expanded = !uiState.isRefreshing
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier.padding(paddingValues),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(uiState.feed) { resource ->
                NewsResourceCard(
                    resource = resource,
                    onBookmarkClick = { onAction(HomeAction.ToggleBookmark(resource.id)) },
                    onClick = { onAction(HomeAction.NavigateToDetail(resource.id)) },
                    modifier = Modifier.padding(horizontal = 16.dp)
                )
            }
            
            if (uiState.isLoadingMore) {
                item {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator()
                    }
                }
            }
        }
    }
}
```

### Shared UI Components

```kotlin
// core/ui/components/NewsResourceCard.kt
@Composable
fun NewsResourceCard(
    resource: UserNewsResource,
    onBookmarkClick: () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier,
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header with bookmark
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = resource.title,
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                
                IconButton(onClick = onBookmarkClick) {
                    Icon(
                        imageVector = if (resource.isBookmarked) {
                            Icons.Filled.Bookmark
                        } else {
                            Icons.Outlined.Bookmark
                        },
                        contentDescription = if (resource.isBookmarked) {
                            "Remove bookmark"
                        } else {
                            "Add bookmark"
                        }
                    )
                }
            }
            
            // Content preview
            Text(
                text = resource.content,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )
            
            // Topics
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                resource.topics.forEach { topic ->
                    TopicChip(topic = topic)
                }
            }
            
            // Metadata
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "Published ${formatDate(resource.publishedAt)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                if (resource.isFollowing) {
                    Badge {
                        Text("Following")
                    }
                }
            }
        }
    }
}
```

## Navigation

### Navigation3 Architecture

```kotlin
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.adaptive.ExperimentalMaterial3AdaptiveApi
import androidx.compose.material3.adaptive.WindowAdaptiveInfo
import androidx.compose.material3.adaptive.currentWindowAdaptiveInfo
import androidx.compose.material3.adaptive.layout.ListDetailPaneScaffold
import androidx.compose.material3.adaptive.layout.ListDetailPaneScaffoldRole
import androidx.compose.material3.adaptive.layout.rememberListDetailPaneScaffoldState
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffoldState
import androidx.compose.material3.adaptive.navigationsuite.rememberNavigationSuiteScaffoldState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation3.NavHost
import androidx.navigation3.compose.rememberNavController

@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    val navigationSuiteScaffoldState = rememberNavigationSuiteScaffoldState()
    
    // Create navigators in app module
    val authNavigator = remember {
        object : AuthNavigator {
            override fun navigateToHome() {
                navController.navigate("home") {
                    popUpTo("auth") { inclusive = true }
                }
            }
            override fun navigateToRegister() = navController.navigate("auth/register")
            override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
            override fun navigateBack() = navController.popBackStack()
            override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
            override fun navigateToMainApp() {
                navController.navigate("main") {
                    popUpTo("auth") { inclusive = true }
                }
            }
            override fun navigateToVerifyEmail(token: String) = navController.navigate("auth/verify/$token")
            override fun navigateToResetPassword(token: String) = navController.navigate("auth/reset/$token")
        }
    }
    
    NavigationSuiteScaffold(
        state = navigationSuiteScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        navigationSuiteItems = {
            item(
                icon = androidx.compose.material.icons.Icons.Default.Home,
                label = "Home",
                selected = navController.currentDestination?.route?.startsWith("home") == true ||
                          navController.currentDestination?.route == "main",
                onClick = { navController.navigate("home") }
            )
            item(
                icon = androidx.compose.material.icons.Icons.Default.Person,
                label = "Profile",
                selected = navController.currentDestination?.route?.startsWith("profile") == true,
                onClick = { navController.navigate("profile/current") }
            )
            item(
                icon = androidx.compose.material.icons.Icons.Default.Settings,
                label = "Settings",
                selected = navController.currentDestination?.route?.startsWith("settings") == true,
                onClick = { navController.navigate("settings") }
            )
        }
    ) {
        NavHost(
            navController = navController,
            startDestination = "auth",
            modifier = Modifier.fillMaxSize()
        ) {
            authGraph(authNavigator)
            homeGraph(
                homeNavigator = remember {
                    object : HomeNavigator {
                        override fun navigateToDetails(itemId: String) = 
                            navController.navigate("home/details/$itemId")
                        override fun navigateBack() = navController.popBackStack()
                    }
                }
            )
            settingsGraph()
            
            // Main app screen (could be tab navigation)
            composable("main") {
                MainAppScreen(
                    onLogout = {
                        navController.navigate("auth") {
                            popUpTo("main") { inclusive = true }
                        }
                    }
                )
            }
            
            // Profile feature
            composable(
                route = "profile/{userId}",
                arguments = listOf(navArgument("userId") { type = NavType.StringType })
            ) { backStackEntry ->
                ProfileScreen(
                    userId = backStackEntry.arguments?.getString("userId") ?: "",
                    onNavigateBack = { navController.popBackStack() }
                )
            }
        }
    }
}

// For list-detail layouts (tablets, foldables)
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigationWithListDetail(
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
    val navController = rememberNavController()
    val listDetailPaneScaffoldState = rememberListDetailPaneScaffoldState()
    
    ListDetailPaneScaffold(
        state = listDetailPaneScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        listPane = {
            // Left pane - list view
            Column(modifier = Modifier.fillMaxSize()) {
                // List items that can navigate to detail
            }
        },
        detailPane = {
            // Right pane - detail view
            NavHost(
                navController = navController,
                startDestination = "auth"
            ) {
                authGraph(/* ... */)
                // Other graphs
            }
        }
    )
}

// Simple version without adaptive UI (if needed)
@Composable
fun AppNavigationSimple() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "auth"
    ) {
        authGraph(
            authNavigator = remember {
                object : AuthNavigator {
                    override fun navigateToHome() = navController.navigate("home")
                    override fun navigateToRegister() = navController.navigate("auth/register")
                    override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
                    override fun navigateBack() = navController.popBackStack()
                    override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
                    override fun navigateToMainApp() = navController.navigate("main")
                    override fun navigateToVerifyEmail(token: String) = navController.navigate("auth/verify/$token")
                    override fun navigateToResetPassword(token: String) = navController.navigate("auth/reset/$token")
                }
            }
        )
        homeGraph(
            homeNavigator = remember {
                object : HomeNavigator {
                    override fun navigateToDetails(itemId: String) = navController.navigate("home/details/$itemId")
                    override fun navigateBack() = navController.popBackStack()
                }
            }
        )
        // Other feature graphs
    }
}
```

#### AuthDestination.kt (`navigation/`)
```kotlin
sealed class AuthDestination(val route: String) {
    object Login : AuthDestination("auth/login")
    object Register : AuthDestination("auth/register")
    object ForgotPassword : AuthDestination("auth/forgot_password")
    
    object Profile : AuthDestination("auth/profile/{userId}") {
        fun createRoute(userId: String) = "auth/profile/$userId"
    }
    
    object VerifyEmail : AuthDestination("auth/verify/{token}") {
        fun createRoute(token: String) = "auth/verify/$token"
    }
    
    companion object {
        fun fromRoute(route: String?): AuthDestination? {
            return when {
                route?.startsWith("auth/profile/") == true -> Profile
                route?.startsWith("auth/verify/") == true -> VerifyEmail
                route == Login.route -> Login
                route == Register.route -> Register
                route == ForgotPassword.route -> ForgotPassword
                else -> null
            }
        }
    }
}
```

#### AuthNavigator.kt (`navigation/`)
```kotlin
interface AuthNavigator {
    // Navigation to other screens within this feature
    fun navigateToRegister()
    fun navigateToForgotPassword()
    fun navigateBack()
    
    // Navigation to other features (implemented in app module)
    fun navigateToHome()
    fun navigateToProfile(userId: String)
    fun navigateToMainApp()
    
    // Deep link navigation
    fun navigateToVerifyEmail(token: String)
    fun navigateToResetPassword(token: String)
}
```

#### AuthGraph.kt (`navigation/`)
```kotlin
fun NavGraphBuilder.authGraph(
    authNavigator: AuthNavigator,
    startDestination: String = AuthDestination.Login.route
) {
    composable(
        route = AuthDestination.Login.route,
        arguments = listOf(
            navArgument("deepLinkToken") {
                type = NavType.StringType
                nullable = true
                defaultValue = null
            }
        )
    ) { backStackEntry ->
        val deepLinkToken = backStackEntry.arguments?.getString("deepLinkToken")
        
        LoginScreen(
            deepLinkToken = deepLinkToken,
            onLoginSuccess = { user ->
                authNavigator.navigateToMainApp()
            },
            onRegisterClick = {
                authNavigator.navigateToRegister()
            },
            onForgotPasswordClick = {
                authNavigator.navigateToForgotPassword()
            }
        )
    }
    
    composable(route = AuthDestination.Register.route) {
        RegisterScreen(
            onRegisterSuccess = { user ->
                authNavigator.navigateToMainApp()
            },
            onNavigateToLogin = {
                authNavigator.navigateBack()
            }
        )
    }
    
    composable(route = AuthDestination.ForgotPassword.route) {
        ForgotPasswordScreen(
            onResetSuccess = {
                authNavigator.navigateBack()
            },
            onNavigateBack = {
                authNavigator.navigateBack()
            }
        )
    }
    
    composable(
        route = AuthDestination.VerifyEmail.route,
        arguments = listOf(navArgument("token") { type = NavType.StringType })
    ) { backStackEntry ->
        val token = backStackEntry.arguments?.getString("token")
        VerifyEmailScreen(
            token = token ?: "",
            onVerificationComplete = {
                authNavigator.navigateToLogin()
            }
        )
    }
}
```

### When to Use Navigation3:
- **All new Compose projects should use Navigation3** as it's the modern navigation API
- Building responsive UIs for phones, tablets, foldables, or desktop
- Need automatic navigation adaptation with `NavigationSuiteScaffold`
- Want Material 3 adaptive navigation patterns and list-detail layouts
- **Important**: Navigation3 is currently in beta (1.4.0-beta01), suitable for production but expect minor API changes

### Key Benefits of Navigation3 Architecture:

1. **Feature Independence**: Features don't depend on each other; only app module coordinates navigation via `Navigator` interfaces
2. **Type-Safe Navigation**: Sealed `Destination` classes with `createRoute()` functions
3. **Testable Navigation**: `Navigator` interfaces allow easy mocking without NavController dependencies
4. **Adaptive UI**: `NavigationSuiteScaffold` automatically adapts between navigation bar, rail, and drawer based on `windowAdaptiveInfo`
5. **Single Backstack**: One `NavHost` controls entire app flow within `NavigationSuiteScaffold`
6. **Material 3 Integration**: Built-in support for Material 3 adaptive design with `ListDetailPaneScaffold`
7. **Modern API**: Latest navigation patterns including support for predictive back gestures
8. **Multi-pane Support**: Native support for list-detail layouts on tablets and foldables
9. **Window Adaptive Integration**: Direct access to `windowAdaptiveInfo` for responsive layouts
10. **Predictive Back Gestures**: Built-in support for Android's predictive back gesture system
11. **Compose-First Design**: Designed specifically for Jetpack Compose, not adapted from View system
12. **`windowAdaptiveInfo`**: Provides screen size/type information for adaptive decisions
13. **`ListDetailPaneScaffold`**: For tablet/foldable list-detail layouts
14. **`NavHost` from `androidx.navigation3`**: The Navigation3 version of NavHost
15. **`composable` from `androidx.navigation3.compose`**: Navigation3's composable destination

### Migration Note:
If migrating from Navigation 2.x to Navigation3:
1. Update imports from `androidx.navigation.*` to `androidx.navigation3.*`
2. Add `windowAdaptiveInfo` parameter to `NavigationSuiteScaffold`
3. Update `NavHost` and `rememberNavController()` imports
4. Consider implementing `ListDetailPaneScaffold` for tablet-optimized layouts

## Complete Architecture Flow

### User Interaction Flow (UI → Data):
```
User Action → Screen → ViewModel → UseCase → Repository → Data Source
   (Event)   (UI)    (State)   (Business)  (Access)   (Persistence)
      ↓        ↓         ↓          ↓           ↓            ↓
   Click → Composable → Process → Transform → Retrieve → Local/Remote
```

### Data Response Flow (Data → UI):
```
Data Source → Repository → UseCase → ViewModel → UiState → Screen
   (Change)    (Update)   (Combine)   (Update)   (State)   (Render)
       ↓           ↓          ↓          ↓          ↓         ↓
  DB Update → Map Data → Business Logic → StateFlow → Observe → Recomposition
```

### Navigation Flow (Feature Coordination):
```
User Action → Screen → Navigator Interface → App Module → Navigation3
   (Navigate)   (Call)     (Contract)      (Implementation)  (Routing)
       ↓           ↓             ↓                ↓             ↓
   Tap Link → Call navigate() → Interface → App Navigator → NavController → Destination
```

## Combined Complete Flow Diagram:

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION FLOW                                 │
│                                                                                    │
│  User Action (Event)                                                               │
│         ↓                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                             PRESENTATION LAYER                             │    │
│  │  ┌─────────────┐  ┌─────────────────────────┐  ┌──────────────────────┐    │    │
│  │  │   Screen    │  │      ViewModel          │  │    Navigator         │    │    │
│  │  │ (Composable)│  │  (StateFlow<UiState>)   │  │   (Interface)        │    │    │
│  │  └─────┬───────┘  └───────────┬─────────────┘  └──────────┬───────────┘    │    │
│  │        │                      │                           │                │    │
│  └────────┼──────────────────────┼───────────────────────────┼────────────────┘    │
│           │ onAction()           │ updateUiState()           │ navigate()          │
├───────────┼──────────────────────┼───────────────────────────┼─────────────────────┤
│           │                      │                           │                     │
│  ┌────────▼──────────┐ ┌─────────▼──────────┐      ┌─────────▼──────────────┐      │
│  │    DOMAIN LAYER   │ │    DATA LAYER      │      │    NAVIGATION          │      │
│  │  ┌─────────────┐  │ │  ┌──────────────┐  │      │  (App Module)          │      │
│  │  │   UseCase   │  │ │  │  Repository  │  │      │  ┌──────────────────┐  │      │
│  │  │ (Business)  │  │ │  │ (Data Access)│  │      │  │ App Navigator    │  │      │
│  │  └──────┬──────┘  │ │  └──────┬───────┘  │      │  │ (Implementation) │  │      │
│  │         │ invoke()│ │         │ getData()│      │  └──────────┬───────┘  │      │
│  └─────────┼─────────┘ └─────────┼──────────┘      └─────────────┼──────────┘      │
│            │                     │                               │                 │
│  ┌─────────▼─────────────────────▼───────────────────────────────▼──────────────┐  │
│  │                    DATA SOURCES / NAVIGATION ENGINE                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │  Local Storage  │  │  Remote API     │  │  Navigation3                 │  │  │
│  │  │   (Room)        │  │   (Retrofit)    │  │  (NavController)             │  │  │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                              DATA RESPONSE FLOW                                    │
│                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                    REACTIVE DATA STREAM                                    │    │
│  │                                                                            │    │
│  │  Data Change (Local/Remote) → Repository Flow → UseCase Transform →        │    │
│  │  ViewModel StateFlow → Screen Observation → UI Recomposition               │    │
│  │                                                                            │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                              NAVIGATION RESPONSE FLOW                              │
│                                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    ADAPTIVE UI RENDERING                                    │   │
│  │                                                                             │   │
│  │  Navigation3 Route → Feature Graph → Screen Destination →                   │   │
│  │  NavigationSuiteScaffold → Adaptive Layout → UI Render                      │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Flow Rules:

### 1. **Unidirectional Event Flow (DOWN):**
```
User Action → Screen → ViewModel → UseCase → Repository → Data Source
     ↓           ↓         ↓         ↓          ↓           ↓
  Tap/Click → Handle → Process → Business → Data Access → Persist/Request
```

### 2. **Unidirectional Data Flow (UP):**
```
Data Source → Repository → UseCase → ViewModel → UiState → Screen → UI
     ↓           ↓         ↓         ↓          ↓         ↓       ↓
  DB/Network → Map → Combine → Update → Observe → Render → Display
```

### 3. **Unidirectional Navigation Flow:**
```
Screen → Navigator Interface → App Module → Navigation3 → Destination Screen
   ↓            ↓                  ↓            ↓             ↓
Call navigate() → Contract → Implementation → Routing → Render New UI
```

## Concrete Example Flow: Bookmarking a News Item

### Phase 1: User Interaction (Event Flow DOWN)
```
1. User taps bookmark icon on news card
2. Screen: HomeScreen calls viewModel.onAction(ToggleBookmark("news-123"))
3. ViewModel: HomeViewModel processes action in viewModelScope
4. UseCase: Calls BookmarkNewsUseCase("news-123", true)
5. Repository: UserDataRepository.updateBookmark("news-123", true)
6. Data Source: DataStore writes preference, Room updates if needed
```

### Phase 2: Data Response (Data Flow UP)
```
1. DataStore: Emits preference change via Flow
2. Repository: UserDataRepository.userData Flow updates
3. UseCase: GetUserNewsResourcesUseCase combines with news Flow
4. ViewModel: Receives updated Flow, updates uiState
5. Screen: Observes uiState change, recomposes news card
6. UI: Bookmark icon changes from outline to filled
```

### Phase 3: Navigation Example (Separate Flow)
```
1. User taps news card
2. Screen: Calls homeNavigator.navigateToDetail("news-123")
3. Navigator Interface: HomeNavigator.navigateToDetail() contract
4. App Module: AppNavigator implementation routes to "home/detail/news-123"
5. Navigation3: NavController navigates to detail destination
6. Feature Graph: Renders NewsDetailScreen
7. UI: Shows news detail view
```

This architecture ensures:
- **Responsive UI**: Immediate optimistic updates
- **Data consistency**: Single source of truth in local database
- **Offline support**: Works without network connection
- **Testability**: Each layer can be tested independently
- **Scalability**: Modular structure supports feature growth
- **Modern patterns**: Navigation3, Material3 adaptive design, predictive back gestures
- **Features are independent** (no feature-to-feature dependencies)
- **Navigation is coordinated centrally** (app module)
- **Data flows through defined layers** (UI → Domain → Data)
- **Each concern has clear boundaries** (navigation vs. business logic vs. UI rendering)