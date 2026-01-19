# Jetpack Compose Patterns

Modern UI patterns following Google's Material 3 guidelines with Navigation3, adaptive layouts, and our modular architecture.

## Table of Contents
1. [Screen Architecture](#screen-architecture)
2. [State Management](#state-management)
3. [Component Patterns](#component-patterns)
4. [Navigation with Navigation3](#navigation-with-navigation3)
5. [Adaptive UI](#adaptive-ui)
6. [Theming & Design System](#theming--design-system)
7. [Previews & Testing](#previews--testing)
8. [Performance Optimization](#performance-optimization)

## Screen Architecture

### Feature Screen Pattern

Separate navigation, state management, and pure UI concerns with our modular approach:

```kotlin
// feature-home/presentation/HomeRoute.kt
@Composable
fun HomeRoute(
    onNavigateToDetail: (String) -> Unit,
    onNavigateToSettings: () -> Unit,
    onNavigateToProfile: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Handle navigation actions from ViewModel
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
    
    HomeScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        modifier = modifier
    )
}

// feature-home/presentation/HomeScreen.kt
@Composable
fun HomeScreen(
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
```

### Benefits with Our Architecture:
- **Feature Isolation**: Screens are self-contained within feature modules
- **Testable Components**: Pure UI without ViewModel dependencies
- **Navigation Decoupling**: Screens call Navigator interfaces, not NavController directly
- **Lifecycle Awareness**: Built-in support with `collectAsStateWithLifecycle()`
- **Adaptive Ready**: Designed for `NavigationSuiteScaffold` and responsive layouts

## State Management

### Sealed Interface for UI State

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

### Actions Pattern for User Interactions

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

### Modern ViewModel with Optimistic Updates

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
                
                // Actual update with proper error handling
                bookmarkNewsUseCase(resourceId, updatedResource.isBookmarked)
                    .onFailure { e ->
                        // Revert on failure
                        currentFeed[index] = resource
                        _uiState.value = currentState.copy(feed = currentFeed)
                    }
            }
        }
    }
}
```

### State Collection with Lifecycle

```kotlin
@Composable
fun HomeRoute(viewModel: HomeViewModel = hiltViewModel()) {
    // Lifecycle-aware state collection
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Coroutine scope for handling actions
    val coroutineScope = rememberCoroutineScope()
    
    HomeScreen(
        uiState = uiState,
        onAction = { action ->
            coroutineScope.launch {
                viewModel.onAction(action)
            }
        }
    )
}
```

## Component Patterns

### Stateless, Reusable Components

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
            
            // Content preview with proper ellipsis
            Text(
                text = resource.content,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )
            
            // Topics with FlowRow for wrapping
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                resource.topics.forEach { topic ->
                    TopicChip(topic = topic)
                }
            }
            
            // Metadata row
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

### Adaptive List Components

```kotlin
// core/ui/components/NewsFeed.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun NewsFeed(
    feed: List<UserNewsResource>,
    isLoadingMore: Boolean = false,
    onBookmarkClick: (String) -> Unit,
    onItemClick: (String) -> Unit,
    onLoadMore: () -> Unit,
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo(),
    modifier: Modifier = Modifier
) {
    val isWideScreen = windowAdaptiveInfo.windowSizeClass.widthSizeClass != WindowWidthSizeClass.Compact
    
    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(horizontal = if (isWideScreen) 32.dp else 16.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        items(
            items = feed,
            key = { it.id }
        ) { resource ->
            NewsResourceCard(
                resource = resource,
                onBookmarkClick = { onBookmarkClick(resource.id) },
                onClick = { onItemClick(resource.id) },
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        if (isLoadingMore) {
            item {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(48.dp))
                }
            }
        }
        
        // Load more trigger
        item {
            LaunchedEffect(Unit) {
                onLoadMore()
            }
        }
    }
}
```

### Shared Loading & Error States

```kotlin
// core/ui/components/loading/
@Composable
fun LoadingScreen(
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            CircularProgressIndicator()
            Text(
                text = "Loading...",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun ErrorContent(
    uiState: HomeUiState.Error,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Icon(
                imageVector = when (uiState.errorType) {
                    ErrorType.Network -> Icons.Outlined.WifiOff
                    ErrorType.Server -> Icons.Outlined.ErrorOutline
                    ErrorType.Database -> Icons.Outlined.Storage
                    else -> Icons.Outlined.Warning
                },
                contentDescription = "Error",
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.error
            )
            
            Text(
                text = uiState.message,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center
            )
            
            if (uiState.canRetry) {
                Button(onClick = onRetry) {
                    Text("Retry")
                }
            }
        }
    }
}
```

## Navigation with Navigation3

### Modern Navigation with Adaptive UI

```kotlin
// app/AppNavigation.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    val navigationSuiteScaffoldState = rememberNavigationSuiteScaffoldState()
    
    // Create navigator implementations in app module
    val homeNavigator = remember {
        object : HomeNavigator {
            override fun navigateToDetail(resourceId: String) = 
                navController.navigate("home/detail/$resourceId")
            override fun navigateBack() = navController.popBackStack()
            override fun navigateToSettings() = navController.navigate("settings")
            override fun navigateToProfile() = navController.navigate("profile")
        }
    }
    
    NavigationSuiteScaffold(
        state = navigationSuiteScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        navigationSuiteItems = {
            item(
                icon = Icons.Default.Home,
                label = "Home",
                selected = navController.currentDestination?.route?.startsWith("home") == true,
                onClick = { navController.navigate("home") }
            )
            item(
                icon = Icons.Default.Person,
                label = "Profile",
                selected = navController.currentDestination?.route?.startsWith("profile") == true,
                onClick = { navController.navigate("profile") }
            )
            item(
                icon = Icons.Default.Settings,
                label = "Settings",
                selected = navController.currentDestination?.route?.startsWith("settings") == true,
                onClick = { navController.navigate("settings") }
            )
        }
    ) {
        NavHost(
            navController = navController,
            startDestination = "home",
            modifier = Modifier.fillMaxSize()
        ) {
            homeGraph(homeNavigator)
            profileGraph()
            settingsGraph()
        }
    }
}
```

### Feature Navigation Setup

```kotlin
// feature-home/navigation/HomeGraph.kt
fun NavGraphBuilder.homeGraph(homeNavigator: HomeNavigator) {
    composable(
        route = HomeDestination.Home.route
    ) {
        HomeRoute(
            onNavigateToDetail = homeNavigator::navigateToDetail,
            onNavigateToSettings = homeNavigator::navigateToSettings,
            onNavigateToProfile = homeNavigator::navigateToProfile
        )
    }
    
    composable(
        route = HomeDestination.Detail.route,
        arguments = listOf(navArgument("resourceId") { type = NavType.StringType })
    ) { backStackEntry ->
        val resourceId = backStackEntry.arguments?.getString("resourceId") ?: ""
        NewsDetailScreen(
            resourceId = resourceId,
            onNavigateBack = homeNavigator::navigateBack
        )
    }
}

// feature-home/navigation/HomeDestination.kt
sealed class HomeDestination(val route: String) {
    object Home : HomeDestination("home")
    
    object Detail : HomeDestination("home/detail/{resourceId}") {
        fun createRoute(resourceId: String) = "home/detail/$resourceId"
    }
}
```

### Navigator Interface Pattern

```kotlin
// feature-home/navigation/HomeNavigator.kt
interface HomeNavigator {
    fun navigateToDetail(resourceId: String)
    fun navigateBack()
    fun navigateToSettings()
    fun navigateToProfile()
}
```

## Adaptive UI

### Responsive Layouts with Navigation3

```kotlin
// app/AdaptiveAppNavigation.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AdaptiveAppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    
    // Choose appropriate scaffold based on screen size
    when (windowAdaptiveInfo.windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> {
            // Mobile: Bottom navigation
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Compact navigation items
                }
            ) {
                // NavHost content
            }
        }
        WindowWidthSizeClass.Medium -> {
            // Tablet: Navigation rail
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Medium navigation items
                }
            ) {
                // NavHost content
            }
        }
        WindowWidthSizeClass.Expanded -> {
            // Desktop: Navigation drawer
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Expanded navigation items
                }
            ) {
                // NavHost content
            }
        }
    }
}
```

### List-Detail Layouts for Tablets

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun NewsListDetailLayout(
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
    val listDetailPaneScaffoldState = rememberListDetailPaneScaffoldState()
    
    ListDetailPaneScaffold(
        state = listDetailPaneScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        listPane = {
            // List view - scrollable feed
            LazyColumn {
                items(newsItems) { item ->
                    NewsListItem(
                        item = item,
                        onClick = {
                            // Update detail pane
                        }
                    )
                }
            }
        },
        detailPane = {
            // Detail view - shows selected item
            NewsDetailScreen(
                item = selectedItem,
                onBackClick = {
                    // Handle back navigation in detail pane
                }
            )
        }
    )
}
```

## Theming & Design System

### Modern Material 3 Theme

```kotlin
// core/ui/theme/AppTheme.kt
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = darkTheme
        }
    }
    
    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### Custom Design Tokens

```kotlin
// core/ui/theme/AppTypography.kt
val AppTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 57.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp,
    ),
    displayMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 45.sp,
        lineHeight = 52.sp,
        letterSpacing = 0.sp,
    ),
    displaySmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 36.sp,
        lineHeight = 44.sp,
        letterSpacing = 0.sp,
    ),
    // Add other text styles...
)
```

### Component-Specific Themes

```kotlin
// core/ui/components/ButtonStyles.kt
@Composable
fun PrimaryButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    text: @Composable () -> Unit,
    icon: @Composable (() -> Unit)? = null
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary
        ),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 12.dp)
    ) {
        if (icon != null) {
            icon()
            Spacer(modifier = Modifier.width(8.dp))
        }
        text()
    }
}
```

## Previews & Testing

### Comprehensive Preview Setup

```kotlin
// Preview annotations for different configurations
@Preview(name = "Light Mode")
@Preview(name = "Dark Mode", uiMode = Configuration.UI_MODE_NIGHT_YES)
annotation class ThemePreviews

@Preview(name = "Phone", device = Devices.PHONE)
@Preview(name = "Tablet", device = Devices.TABLET)
@Preview(name = "Desktop", device = Devices.DESKTOP)
annotation class DevicePreviews

@Preview(name = "English", locale = "en")
@Preview(name = "Arabic", locale = "ar")
annotation class LocalePreviews
```

### Preview with Realistic Data

```kotlin
// feature-home/presentation/preview/HomeScreenPreview.kt
@ThemePreviews
@DevicePreviews
@Composable
fun HomeScreenPreview() {
    AppTheme {
        HomeScreen(
            uiState = HomeUiState.Success(
                feed = listOf(
                    UserNewsResource(
                        id = "1",
                        title = "Jetpack Compose Best Practices",
                        content = "Learn modern Android UI development with Jetpack Compose...",
                        publishedAt = Instant.now(),
                        topics = listOf(
                            Topic(id = "android", name = "Android", description = "Android development"),
                            Topic(id = "compose", name = "Compose", description = "Jetpack Compose")
                        ),
                        isBookmarked = true,
                        isFollowing = false
                    ),
                    UserNewsResource(
                        id = "2",
                        title = "Navigation3 Adaptive UI",
                        content = "Build responsive apps with Navigation3 and Material 3...",
                        publishedAt = Instant.now().minus(Duration.ofDays(1)),
                        topics = listOf(
                            Topic(id = "navigation", name = "Navigation", description = "Android Navigation")
                        ),
                        isBookmarked = false,
                        isFollowing = true
                    )
                )
            ),
            onAction = { },
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

### Preview Parameter Providers

```kotlin
class HomeUiStatePreviewParameterProvider : PreviewParameterProvider<HomeUiState> {
    override val values: Sequence<HomeUiState> = sequenceOf(
        HomeUiState.Loading,
        HomeUiState.Success(
            feed = emptyList(),
            selectedTopic = null,
            isRefreshing = false,
            isLoadingMore = false
        ),
        HomeUiState.Error(
            message = "Network connection lost",
            canRetry = true,
            errorType = ErrorType.Network
        ),
        HomeUiState.Empty
    )
}

@ThemePreviews
@Composable
fun HomeScreenAllStatesPreview(
    @PreviewParameter(HomeUiStatePreviewParameterProvider::class) uiState: HomeUiState
) {
    AppTheme {
        HomeScreen(
            uiState = uiState,
            onAction = { },
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

## Performance Optimization

### Lazy Composition

```kotlin
@Composable
fun NewsFeedOptimized(
    feed: List<UserNewsResource>,
    onBookmarkClick: (String) -> Unit,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(
            items = feed,
            key = { it.id } // Essential for stable keys
        ) { resource ->
            // Use derivedStateOf for expensive calculations
            val formattedDate by remember(resource.publishedAt) {
                derivedStateOf {
                    formatDate(resource.publishedAt)
                }
            }
            
            NewsResourceCard(
                resource = resource.copy(
                    // Pass pre-formatted data to avoid recomposition
                    formattedDate = formattedDate
                ),
                onBookmarkClick = { onBookmarkClick(resource.id) },
                onClick = { onItemClick(resource.id) }
            )
        }
    }
}
```

### State Hoisting for Performance

```kotlin
@Composable
fun SearchableNewsFeed(
    initialFeed: List<UserNewsResource>,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }
    
    // Hoist expensive filtering
    val filteredFeed by remember(initialFeed, searchQuery) {
        derivedStateOf {
            if (searchQuery.isEmpty()) {
                initialFeed
            } else {
                initialFeed.filter { resource ->
                    resource.title.contains(searchQuery, ignoreCase = true) ||
                    resource.content.contains(searchQuery, ignoreCase = true)
                }
            }
        }
    }
    
    Column(modifier = modifier) {
        SearchBar(
            query = searchQuery,
            onQueryChange = { searchQuery = it }
        )
        
        NewsFeed(
            feed = filteredFeed,
            onBookmarkClick = { /* ... */ },
            onItemClick = { /* ... */ }
        )
    }
}
```

### Remember/Lambda Best Practices

```kotlin
@Composable
fun NewsResourceCardOptimized(
    resource: UserNewsResource,
    onBookmarkClick: (String) -> Unit,
    onClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    // Use rememberUpdatedState for lambdas that change
    val currentOnBookmarkClick by rememberUpdatedState(onBookmarkClick)
    val currentOnClick by rememberUpdatedState(onClick)
    
    // Memoize expensive callbacks
    val onBookmarkClickMemoized = remember(resource.id) {
        { currentOnBookmarkClick(resource.id) }
    }
    
    val onClickMemoized = remember(resource.id) {
        { currentOnClick(resource.id) }
    }
    
    Card(
        onClick = onClickMemoized,
        modifier = modifier
    ) {
        // Card content...
        IconButton(
            onClick = onBookmarkClickMemoized,
            modifier = Modifier.noRippleClickable { /* handled by IconButton */ }
        ) {
            // Icon content...
        }
    }
}
```