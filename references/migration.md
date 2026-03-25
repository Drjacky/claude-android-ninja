# Migration Guide

Consolidated migration paths for modernizing Android codebases. Each section shows the legacy
pattern and its modern replacement.

## Table of Contents

1. [XML to Compose](#xml-to-compose)
2. [LiveData to StateFlow](#livedata-to-stateflow)
3. [RxJava to Coroutines](#rxjava-to-coroutines)
4. [Navigation 2.x to Navigation3](#navigation-2x-to-navigation3)
5. [Accompanist to Official APIs](#accompanist-to-official-apis)
6. [Compose API Migrations](#compose-api-migrations)
7. [Material 2 to Material 3](#material-2-to-material-3)
8. [Edge-to-Edge](#edge-to-edge)
9. [Room 2.x to Room 3](#room-2x-to-room-3)

## XML to Compose

### Strategy: Screen-by-Screen

Migrate one screen at a time. Do not attempt a full rewrite. The recommended order:

1. **Leaf screens first** - screens with no child Fragments or complex navigation
2. **Shared components** - extract reusable Composables to `core/ui` as you go
3. **Container screens** - screens that host Fragments or ViewPagers (migrate after children)
4. **Navigation** - migrate to Navigation3 once all screens are Compose

### Compose in XML (Adding Compose to Existing Screens)

Use `ComposeView` to embed Compose inside an XML layout:

```kotlin
// In Fragment or Activity
val composeView = findViewById<ComposeView>(R.id.compose_container)
composeView.setContent {
    AppTheme {
        MyNewComposableComponent(
            state = viewModel.uiState.collectAsStateWithLifecycle().value,
            onAction = viewModel::onAction
        )
    }
}
```

```xml
<!-- In layout XML -->
<androidx.compose.ui.platform.ComposeView
    android:id="@+id/compose_container"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
```

### XML in Compose (Using Legacy Views in Compose Screens)

Use `AndroidView` to embed existing XML views inside Compose:

```kotlin
@Composable
fun LegacyMapView(modifier: Modifier = Modifier) {
    AndroidView(
        factory = { context ->
            MapView(context).apply {
                onCreate(null)
            }
        },
        update = { mapView ->
            mapView.getMapAsync { map ->
                // configure map
            }
        },
        modifier = modifier
    )
}
```

Use `AndroidView` only for views that have no Compose equivalent (e.g., `MapView`, `WebView`,
`AdView`). For standard UI elements, always use Compose directly.

### Migration Checklist

- Replace `Fragment` + XML layout with a `@Composable` function
- Replace `ViewBinding` / `DataBinding` with Compose state
- Replace `RecyclerView` with `LazyColumn` / `LazyRow`
- Replace `ConstraintLayout` with Compose `Row`, `Column`, `Box` (or `ConstraintLayout` for Compose)
- Replace `styles.xml` theming with `MaterialTheme` (see [android-theming.md](android-theming.md))
- Replace XML string resources usage with `stringResource()` in Compose

## LiveData to StateFlow

### ViewModel Migration

```kotlin
// OLD: LiveData
class UserViewModel : ViewModel() {
    private val _user = MutableLiveData<User>()
    val user: LiveData<User> = _user

    fun loadUser() {
        viewModelScope.launch {
            _user.value = repository.getUser()
        }
    }
}

// NEW: StateFlow
class UserViewModel : ViewModel() {
    private val _user = MutableStateFlow<User?>(null)
    val user: StateFlow<User?> = _user.asStateFlow()

    fun loadUser() {
        viewModelScope.launch {
            _user.value = repository.getUser()
        }
    }
}
```

### UI Collection

```kotlin
// OLD: LiveData observation in Fragment
viewModel.user.observe(viewLifecycleOwner) { user ->
    binding.userName.text = user.name
}

// NEW: StateFlow in Compose
val user by viewModel.user.collectAsStateWithLifecycle()
UserScreen(user = user)
```

### Transformations

```kotlin
// OLD: LiveData transformations
val userName: LiveData<String> = user.map { it.name }
val userDetails: LiveData<Details> = user.switchMap { repository.getDetails(it.id) }

// NEW: Flow operators
val userName: StateFlow<String> = user.map { it?.name.orEmpty() }
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "")

val userDetails: StateFlow<Details?> = user
    .filterNotNull()
    .flatMapLatest { repository.getDetails(it.id) }
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)
```

### Key Differences

- `LiveData` requires an initial observer to emit; `StateFlow` always has a value (requires initial state)
- `LiveData.observe()` is lifecycle-aware by default; use `collectAsStateWithLifecycle()` for the same behavior with Flow
- `StateFlow` uses `SharingStarted.WhileSubscribed(5_000)` to survive configuration changes

## RxJava to Coroutines

### Coexistence (Migration Not Yet Planned)

When maintaining projects with both RxJava and Coroutines, expose UI state via `StateFlow`
regardless of the underlying implementation:

```kotlin
@HiltViewModel
class ProductsViewModel @Inject constructor(
    private val getProductsUseCase: GetProductsUseCase,
    private val disposables: CompositeDisposable
) : ViewModel() {

    private val _uiState = MutableStateFlow<ProductsUiState>(ProductsUiState.Loading)
    val uiState: StateFlow<ProductsUiState> = _uiState.asStateFlow()

    fun loadProducts() {
        getProductsUseCase.execute()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(
                { products ->
                    _uiState.value = ProductsUiState.Success(products)
                },
                { error ->
                    _uiState.value = ProductsUiState.Error(error.message ?: "Unknown error")
                }
            )
            .also { disposables.add(it) }
    }

    override fun onCleared() {
        super.onCleared()
        disposables.clear()
    }
}
```

UI code uses `collectAsStateWithLifecycle()` regardless of whether the ViewModel uses Coroutines
or RxJava:

```kotlin
@Composable
fun ProductsRoute(viewModel: ProductsViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    ProductsScreen(
        state = uiState,
        onRetry = viewModel::loadProducts
    )
}
```

### Disposal Management

**Option 1: CompositeDisposable (recommended)**

```kotlin
class ProductsViewModel : ViewModel() {
    private val disposables = CompositeDisposable()

    fun loadProducts() {
        getProductsUseCase()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(...)
            .also { disposables.add(it) }
    }

    override fun onCleared() {
        super.onCleared()
        disposables.clear()
    }
}
```

**Option 2: AutoDispose (third-party, requires base ViewModel)**

```kotlin
dependencies {
    implementation(libs.autodispose.android)
    implementation(libs.autodispose.android.archcomponents)
}

class ProductsViewModel : ViewModel(), LifecycleScopeProvider by AndroidLifecycleScopeProvider.from(this) {
    fun loadProducts() {
        getProductsUseCase()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .autoDispose(this)
            .subscribe(...)
    }
}
```

### Paging with RxJava

Use `paging-rxjava3` alongside `paging-compose`:

```kotlin
dependencies {
    implementation(libs.androidx.paging.runtime)
    implementation(libs.androidx.paging.compose)
    implementation(libs.androidx.paging.rxjava3)
}

class ProductsPagingSource(
    private val productsApi: ProductsApi
) : RxPagingSource<Int, Product>() {

    override fun loadSingle(params: LoadParams<Int>): Single<LoadResult<Int, Product>> {
        val page = params.key ?: 1

        return productsApi.getProducts(page, params.loadSize)
            .map { response ->
                LoadResult.Page(
                    data = response.products,
                    prevKey = if (page == 1) null else page - 1,
                    nextKey = if (response.hasMore) page + 1 else null
                ) as LoadResult<Int, Product>
            }
            .onErrorReturn { error ->
                LoadResult.Error(error)
            }
    }

    override fun getRefreshKey(state: PagingState<Int, Product>): Int? {
        return state.anchorPosition?.let { anchorPosition ->
            state.closestPageToPosition(anchorPosition)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(anchorPosition)?.nextKey?.minus(1)
        }
    }
}

// ViewModel bridges to Flow for Compose
class ProductsViewModel @Inject constructor(
    private val productsApi: ProductsApi
) : ViewModel() {
    val products: Flow<PagingData<Product>> = Pager(
        config = PagingConfig(pageSize = 20),
        pagingSourceFactory = { ProductsPagingSource(productsApi) }
    ).flow
        .cachedIn(viewModelScope)
}
```

### Migration Path (When Ready)

When planning RxJava to Coroutines migration:

1. Start with data layer (repositories)
2. Then domain layer (use cases)
3. Finally ViewModels
4. UI layer already uses `StateFlow.collectAsStateWithLifecycle()`, so no changes needed

### Coexistence Best Practices

1. **Unified UI layer**: Always use `StateFlow` for UI state, even when ViewModels use RxJava
2. **Isolate RxJava**: Keep RxJava usage in data/domain layers, convert to `StateFlow` at ViewModel boundary
3. **Dispose properly**: Use AutoDispose or `CompositeDisposable` to prevent leaks
4. **Don't mix in same function**: A function should be either fully Coroutines or fully RxJava, not both
5. **Prefer Coroutines for new code**: Only use RxJava for existing legacy code that won't be migrated

See [RxJava to Coroutines migration guide](https://developer.android.com/kotlin/coroutines/coroutines-adv#additional-resources) for detailed migration strategies.

## Navigation 2.x to Navigation3

### Key Changes

| Navigation 2.x              | Navigation3                                      |
|-----------------------------|--------------------------------------------------|
| `NavHost` + `NavController` | `NavDisplay` + `NavBackStack`                    |
| `composable("route")`       | `entryProvider<NavKey>`                          |
| String or type-safe routes  | `@Serializable` data class implementing `NavKey` |
| `navController.navigate()`  | `backStack.add()`                                |
| `rememberNavController()`   | `rememberNavBackStack(startKey)`                 |
| `popBackStack()`            | `backStack.removeLastOrNull()`                   |

### Migration Steps

1. Update imports from `androidx.navigation.*` to `androidx.navigation3.*`
2. Replace `NavHost` with `NavDisplay` and `rememberNavController()` with `rememberNavBackStack()`
3. Convert route strings/classes to `@Serializable` data classes implementing `NavKey`
4. Replace `composable("route") { }` blocks with `entryProvider<YourKey> { }` entries
5. Replace `navController.navigate(...)` calls with `backStack.add(...)`
6. Use `NavigationSuiteScaffold` for adaptive navigation (it handles switching automatically)
7. Use `NavigableListDetailPaneScaffold` / `NavigableSupportingPaneScaffold` for tablet-optimized layouts

For complete Navigation3 architecture, state management, deep links, and adaptive patterns, see
[android-navigation.md](android-navigation.md).

## Accompanist to Official APIs

All Accompanist libraries listed below are deprecated. Use the official replacements.

### System UI Controller -> enableEdgeToEdge()

```kotlin
// Old (remove accompanist-systemuicontroller dependency)
val systemUiController = rememberSystemUiController()
systemUiController.setSystemBarsColor(color = Color.Transparent)

// New: call in Activity.onCreate() before setContent
enableEdgeToEdge()
```

### Pager -> Foundation HorizontalPager/VerticalPager

```kotlin
// Old (remove accompanist-pager dependency)
val pagerState = rememberPagerState()
HorizontalPager(count = items.size, state = pagerState) { page -> }

// New: Foundation pager (page count is a lambda)
val pagerState = rememberPagerState(pageCount = { items.size })
HorizontalPager(state = pagerState) { page -> }
```

### SwipeRefresh -> PullToRefreshBox

```kotlin
// Old (remove accompanist-swiperefresh dependency)
SwipeRefresh(
    state = rememberSwipeRefreshState(isRefreshing),
    onRefresh = { load() }
) { content() }

// New: Material3 PullToRefreshBox
PullToRefreshBox(
    isRefreshing = isRefreshing,
    onRefresh = { load() }
) { content() }
```

### FlowLayout -> Foundation FlowRow/FlowColumn

```kotlin
// Old (remove accompanist-flowlayout dependency)
FlowRow(mainAxisSize = SizeMode.Expand) {
    items.forEach { Chip(it) }
}

// New: Foundation FlowRow
FlowRow(modifier = Modifier.fillMaxWidth()) {
    items.forEach { Chip(it) }
}
```

### Permissions -> activity-compose

```kotlin
// Old (remove accompanist-permissions dependency)
// import com.google.accompanist.permissions.rememberPermissionState

// New: same API, different dependency (androidx.activity:activity-compose)
val permissionState = rememberPermissionState(Manifest.permission.CAMERA) { granted ->
    // handle result
}
```

## Compose API Migrations

### collectAsState -> collectAsStateWithLifecycle

```kotlin
// Old: collects even when app is backgrounded (wastes resources)
val state by viewModel.uiState.collectAsState()

// New: stops collecting when lifecycle is below STARTED
val state by viewModel.uiState.collectAsStateWithLifecycle()
```

Requires `androidx.lifecycle:lifecycle-runtime-compose`.

### mutableStateOf(0) -> mutableIntStateOf(0)

Primitive specializations avoid boxing overhead:

```kotlin
// Old
var count by remember { mutableStateOf(0) }
var progress by remember { mutableStateOf(0.5f) }
var timestamp by remember { mutableStateOf(0L) }

// New
var count by remember { mutableIntStateOf(0) }
var progress by remember { mutableFloatStateOf(0.5f) }
var timestamp by remember { mutableLongStateOf(0L) }
```

Available: `mutableIntStateOf`, `mutableLongStateOf`, `mutableFloatStateOf`, `mutableDoubleStateOf`.

### animateItemPlacement -> animateItem

```kotlin
// Old
LazyColumn {
    items(items, key = { it.id }) { item ->
        ItemRow(modifier = Modifier.animateItemPlacement())
    }
}

// New: handles insert, remove, and reorder animations
LazyColumn {
    items(items, key = { it.id }) { item ->
        ItemRow(modifier = Modifier.animateItem())
    }
}
```

### Modifier.composed -> Modifier.Node

```kotlin
// Old (deprecated - creates composition scope overhead)
fun Modifier.myModifier(value: Int) = composed {
    val state = remember { mutableStateOf(value) }
    this.background(if (state.value > 0) Color.Blue else Color.Gray)
}

// New: Modifier.Node API (no composition scope)
// See compose-patterns.md > Modifiers > Custom Modifiers with Modifier.Node
```

### String Routes -> Type-Safe Routes -> Navigation3

```kotlin
// Old: string-based navigation (pre Navigation 2.8)
navController.navigate("details/$itemId")

// Migration step: type-safe routes (Navigation 2.8+)
@Serializable data class Details(val itemId: Int)
navController.navigate(Details(itemId = 42))

// Current: Navigation3 (see android-navigation.md)
@Serializable data class ProductDetail(val productId: String) : NavKey
backStack.add(ProductDetail(productId = "42"))
```

### @ExperimentalMaterial3Api Graduations

These APIs are stable - remove `@OptIn` annotations:

- `DatePicker` / `DateRangePicker`
- `TimePicker`
- `ExposedDropdownMenuBox`
- `SearchBar` / `DockedSearchBar`
- `ModalBottomSheet`
- `TopAppBar` / `MediumTopAppBar` / `LargeTopAppBar`

```kotlin
// Old
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyScreen() {
    DatePicker(state = rememberDatePickerState())
}

// New: no opt-in needed
@Composable
fun MyScreen() {
    DatePicker(state = rememberDatePickerState())
}
```

### Scaffold innerPadding (Mandatory)

Since Compose 1.6, `Scaffold` requires using `innerPadding`. Ignoring it causes content overlap
with system bars.

```kotlin
// Bad: ignoring innerPadding (won't compile in modern Compose)
Scaffold(topBar = { TopAppBar { } }) {
    LazyColumn { }
}

// Required: apply innerPadding
Scaffold(topBar = { TopAppBar { } }) { innerPadding ->
    LazyColumn(modifier = Modifier.padding(innerPadding)) { }
}
```

## Material 2 to Material 3

Key changes when migrating from `androidx.compose.material` to `androidx.compose.material3`:

| Material 2                          | Material 3                           |
|-------------------------------------|--------------------------------------|
| `MaterialTheme.colors`              | `MaterialTheme.colorScheme`          |
| `Surface(color = ...)`              | `Surface(color = ...)` (same API)    |
| `TextField`                         | `TextField` (same API, new defaults) |
| `BottomNavigation`                  | `NavigationBar`                      |
| `BottomNavigationItem`              | `NavigationBarItem`                  |
| `TopAppBar`                         | `TopAppBar` (different parameters)   |
| `Scaffold` (no padding requirement) | `Scaffold` (must use `innerPadding`) |

Never mix Material 2 and Material 3 imports in the same module.

For theming setup, see [android-theming.md](android-theming.md).

## Edge-to-Edge

Edge-to-edge is the default on Android 15+ and mandatory on API 36.

```kotlin
// Old: manual system bar padding
Surface(modifier = Modifier.systemBarsPadding()) { }

// New: enableEdgeToEdge() + Scaffold handles it
enableEdgeToEdge()  // in Activity.onCreate()
Scaffold { innerPadding ->
    Content(modifier = Modifier.padding(innerPadding))
}
```

For full edge-to-edge setup including `WindowInsets` handling, see
[compose-patterns.md](compose-patterns.md#edge-to-edge-mandatory-on-api-36).

## Room 2.x to Room 3

Jetpack **Room 2.x** (`androidx.room`) and **Room 3** (`androidx.room3`) use different Maven coordinates and runtime APIs. The target is **Room 3** on Android with **KSP**, a **`SQLiteDriver`**, and **coroutine-first DAOs** (`suspend`, **`Flow`**). Official background: [Room 3 release notes](https://developer.android.com/jetpack/androidx/releases/room3), [Room 3 announcement](https://android-developers.googleblog.com/2026/03/room-30-modernizing-room.html), and [Save data with Room](https://developer.android.com/training/data-storage/room).

### Gradle and artifacts

| Room 2.x                                                            | Room 3                                                                                             |
|---------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `androidx.room:room-runtime`, `room-compiler`, `room-gradle-plugin` | `androidx.room3:room3-runtime`, `room3-compiler`, `room3-gradle-plugin`                            |
| Plugin id `androidx.room` + `room { schemaDirectory(...) }`         | Plugin id `androidx.room3` + `room3 { schemaDirectory(...) }`                                      |
| Optional `room-ktx`                                                 | No separate KTX artifact for the same role; use **`Flow` / `suspend`** on DAOs                     |
| KSP `ksp("androidx.room:room-compiler")`                            | KSP **`ksp("androidx.room3:room3-compiler")`** - Room 3 is **KSP-only** (no kapt/Java AP for Room) |

Add **`androidx.sqlite:sqlite-bundled`** and call **`.setDriver(BundledSQLiteDriver())`** on `Room.databaseBuilder` / `Room.inMemoryDatabaseBuilder`. See `assets/libs.versions.toml.template` and the `app.android.room` convention plugin.

**Paging:** If a DAO returns **`PagingSource`**, add **`androidx.room3:room3-paging`** and **`@DaoReturnTypeConverters(PagingSourceDaoReturnTypeConverter::class)`** on the DAO or `@Database` ([release notes](https://developer.android.com/jetpack/androidx/releases/room3)).

### Packages and generated code

- Replace imports **`androidx.room.*`** with **`androidx.room3.*`** (`RoomDatabase`, `Room`, `@Database`, `@Entity`, `@Dao`, `@Query`, `Migration`, etc.).
- Regenerate with KSP after changing coordinates; update **R8** rules to **`androidx.room3.RoomDatabase`** / **`@androidx.room3.Entity`** (`assets/proguard-rules.pro.template`).

### SupportSQLite and `SQLiteDriver`

Room 3 is backed by the **`androidx.sqlite`** driver APIs. **`SupportSQLiteDatabase`**, **`SupportSQLiteQuery`**, and **`openHelper` / `openHelperFactory`** are gone unless you use the compatibility **`androidx.room3:room3-sqlite-wrapper`** for specific legacy call sites ([release notes](https://developer.android.com/jetpack/androidx/releases/room3)).

- **Callbacks and migrations** that took **`SupportSQLiteDatabase`** should use **`SQLiteConnection`** (or the types your Room 3 version documents for `Migration` / `RoomDatabase.Callback` / `AutoMigrationSpec`).
- **Direct SQL / `Cursor`**: prefer **`RoomDatabase.useReaderConnection`** / **`useWriterConnection`** and prepared statements over raw Android `Cursor` ([release notes](https://developer.android.com/jetpack/androidx/releases/room3)).
- **Transactions:** e.g. **`runInTransaction`**-style usage moves to **`withWriteTransaction`** (see [Room 3 release notes](https://developer.android.com/jetpack/androidx/releases/room3)).
- **Builder options** (e.g. pre-packaged database, query callback, multi-instance invalidation): verify each against the current [Room 3](https://developer.android.com/jetpack/androidx/releases/room3) and [Room training guide](https://developer.android.com/training/data-storage/room) for your AGP/targets; some APIs differ or moved with the driver model.

Step-by-step **SupportSQLite → driver** guidance: [Migrate from SupportSQLite](https://developer.android.com/kotlin/multiplatform/room#migrate) (Android-relevant parts apply even in Android-only apps).

### Invalidation and tests

- **`InvalidationTracker.Observer`** / **`addObserver`** are removed; use **`InvalidationTracker.createFlow`** ([release notes](https://developer.android.com/jetpack/androidx/releases/room3)).
- **Instrumented tests:** `androidx.room3:room3-testing`, **`MigrationTestHelper`** with a **`SQLiteDriver`**, **`SQLiteConnection`**, and **suspend** APIs - see [Test migrations](https://developer.android.com/training/data-storage/room/migrating-db-versions#test) and [`MigrationTestHelper`](https://developer.android.com/reference/kotlin/androidx/room3/testing/MigrationTestHelper). In-repo examples: `references/testing.md`.

### Room 2.x lifecycle (context only)

Room 2.x remains in **maintenance** (bugfixes / dependency updates) while Room 3 is the active line ([blog](https://android-developers.googleblog.com/2026/03/room-30-modernizing-room.html)). Plan upgrades on a branch; align **Kotlin**, **KSP**, and **sqlite** versions with [Room 3 releases](https://developer.android.com/jetpack/androidx/releases/room3).
