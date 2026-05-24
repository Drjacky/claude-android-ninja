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
9. [Legacy splash to Splash Screen API](#legacy-splash-to-splash-screen-api)
10. [Room 2.x to Room 3](#room-2x-to-room-3)
11. [Android 17 (API 37) Migration](#android-17-api-37-migration)

## XML to Compose

### Strategy: Screen-by-Screen

Migrate one screen at a time. Do not attempt a full rewrite. Required order:

1. **Leaf screens first** - screens with no child Fragments or complex navigation
2. **Shared components** - extract reusable Composables to `core/ui` as you go
3. **Container screens** - screens that host Fragments or ViewPagers (migrate after children)
4. **Navigation** - migrate to Navigation3 once all screens are Compose

### Per-Screen Workflow (mandatory)

Run for **every** XML screen being migrated:

1. **Capture a baseline screenshot** of the existing XML UI. Reuse an existing screenshot test if present; otherwise add a minimal **UI Automator** or **Espresso** test that opens the screen and saves a screenshot. This is the diff target for steps 2-4.
2. **Migrate only the minimum theming** required for the screen. Do **not** port the whole `styles.xml` / `themes.xml`. Map only the colors, typography, and shapes used by this screen into `MaterialTheme` (see `references/android-theming.md`). Leave the rest of the XML theme untouched.
3. **Add a `@Preview`** for every new composable. A composable without `@Preview` cannot be diff-verified against step 1.
4. **Diff against baseline.** Iterate until layout and styling match (ignore string content). On parity, write a Compose UI test for the new screen, then run the interop and replacement steps.

Delete the XML layout, drawables, styles, and legacy tests **only after** all references are gone.

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
- Replace `styles.xml` theming with `MaterialTheme` (see `references/android-theming.md`)
- Replace XML string resources usage with `stringResource()` in Compose

### Compose-XML interop (hardening)

**Theme:** Wrap every `ComposeView.setContent { }` root in the same `MaterialTheme` entry used by fully Compose screens ([android-theming.md](android-theming.md)). Forbidden: rely on legacy XML `ThemeOverlay` colors inside Compose without mapping tokens to `MaterialTheme.colorScheme`.

**Focus and IME:** When a legacy `EditText` sits beside `ComposeView`, coordinate `FocusRequester` in Compose with `View.clearFocus` / `requestFocus` on the View side so IME and `windowSoftInputMode` stay aligned with [compose-patterns.md](compose-patterns.md) edge-to-edge and IME sections.

**ViewModel scope:** `ComposeView` inside a `Fragment` uses `hiltViewModel()` on that fragment's graph; avoid activity-scoped ViewModels for nested composables unless navigation explicitly requires it ([architecture.md → ViewModel placement](architecture.md#viewmodel-placement)).

**Testing:** Hybrid screens may pair Espresso or UIAutomator on View subtrees with `createComposeRule` on isolated Compose mounts; otherwise one instrumented screenshot or journey per [testing.md](testing.md) and the baseline workflow in [XML to Compose](#xml-to-compose).

**Long-lived `AndroidView`:** Keep only for surfaces without first-class Compose equivalents (`MapView`, `WebView`, `AdView`, vendor SDK views). Forbidden: wrap `TextView` or `RecyclerView` only to postpone Compose migration.

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

**Option 1: CompositeDisposable** - default. Use unless an existing module already wires AutoDispose.

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

### Coexistence rules

- Use `StateFlow` for UI state. Never expose `Observable`/`Single` from a ViewModel.
- Confine RxJava to data/domain layers. Convert to `StateFlow` at the ViewModel boundary.
- Dispose every subscription via `CompositeDisposable.clear()` in `onCleared()`, or AutoDispose.
- Forbidden: mixing RxJava and coroutines inside the same function.
- New code: coroutines + Flow only. RxJava is permitted only inside legacy modules pending migration.

Reference: [RxJava to Coroutines migration guide](https://developer.android.com/kotlin/coroutines/coroutines-adv#additional-resources).

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

For complete Navigation3 architecture, state management, deep links, and adaptive patterns, see `references/android-navigation.md`.

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
// See references/compose-patterns.md → Modifiers → Custom Modifiers with Modifier.Node
```

### Modifier.onFirstVisible -> Modifier.onVisibilityChanged

Deprecated in Compose 1.11 (April '26). Migrate to [`Modifier.onVisibilityChanged`](https://developer.android.com/reference/kotlin/androidx/compose/ui/layout/package-summary#\(androidx.compose.ui.Modifier\).onVisibilityChanged\(kotlin.Long,kotlin.Float,androidx.compose.ui.layout.LayoutBoundsHolder,kotlin.Function1\)) and track first-visible state manually when needed - `onFirstVisible` re-fires on every scroll pass through a lazy layout.

```kotlin
// Old (deprecated)
Modifier.onFirstVisible { logImpression(item.id) }

// New
var alreadyLogged by remember(item.id) { mutableStateOf(false) }
Modifier.onVisibilityChanged { event ->
    if (!alreadyLogged && event.visibleFraction > 0f) {
        logImpression(item.id)
        alreadyLogged = true
    }
}
```

### String Routes -> Type-Safe Routes -> Navigation3

```kotlin
// Old: string-based navigation (pre Navigation 2.8)
navController.navigate("details/$itemId")

// Migration step: type-safe routes (Navigation 2.8+)
@Serializable data class Details(val itemId: Int)
navController.navigate(Details(itemId = 42))

// Current: Navigation3 (see references/android-navigation.md)
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
// WRONG: ignoring innerPadding (does not compile on Compose 1.6+)
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

For theming setup, see `references/android-theming.md`.

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

For full edge-to-edge setup including `WindowInsets` handling, see `references/compose-patterns.md` → "Edge-to-Edge (Mandatory on API 36)".

## Legacy splash to Splash Screen API

Required: Migrate off `android:windowBackground`-only splash themes and off dedicated splash `Activity` stacks before relying on Android 12+ launch behavior. Read [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen) and [Migrate to the Splash Screen API](https://developer.android.com/develop/ui/views/launch/splash-screen/migrate) for current attributes and activity patterns.

On API 31+, the system always draws a splash on cold and warm start. A legacy drawable-only launcher theme may be replaced by the default system treatment; a separate `SplashActivity` yields **system splash then your activity** (double splash).

Required: Add `androidx.core:core-splashscreen` (version catalog: `assets/libs.versions.toml.template`, wiring: `references/gradle-setup.md`). Use the compat library so the same themed splash applies across API levels; platform-only `SplashScreen` without compat leaves pre-12 behavior unchanged.

Required routing (launcher activity):

- Manifest: set `android:theme` on the **LAUNCHER** activity to a style whose parent is `Theme.SplashScreen` (or `Theme.SplashScreen.IconBackground` when a circular plate behind the icon is required).
- Theme: set `windowSplashScreenAnimatedIcon`, `windowSplashScreenBackground`, and `postSplashScreenTheme` to the normal app theme per the current attribute list on [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen).
- Activity `onCreate`: call `installSplashScreen()` **before** `super.onCreate(savedInstanceState)`.

Use `Theme.SplashScreen.IconBackground` when the foreground artwork is transparent and must sit on a solid circular icon background.

**Routing-only activity** (deep link / auth gate): keep a thin activity if routing demands it; hide its content while the system splash stays up, then `startActivity` the real target and `finish()`.

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    val splashScreen = installSplashScreen()
    super.onCreate(savedInstanceState)
    splashScreen.setKeepOnScreenCondition { true }
    startActivity(Intent(this, MainActivity::class.java))
    finish()
}
```

**Branding-only second activity:** Prefer a single splash via theme attributes (`windowSplashScreenBrandingImage` where supported). If a second screen remains for branding, use `setOnExitAnimationListener` for a controlled handoff per [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen). Show dialogs only on the destination activity **after** the system splash is gone.

**Indeterminate startup:** Forbidden: hold the splash for open-ended network work. Dismiss when local readiness is known; use in-app placeholders or skeleton UI for long or unknown-duration loads ([Migrate](https://developer.android.com/develop/ui/views/launch/splash-screen/migrate)).

**Forbidden:**

- `Thread.sleep()`, `Handler.postDelayed()`, or coroutine `delay()` used only to stretch splash time.
- Heavy work, I/O, network, allocations, or `runBlocking` inside `setKeepOnScreenCondition { }`. Multiple cheap flag reads are allowed; blocking or unbounded work is not.

**Launcher vs splash asset:** Use the same drawable as the launcher adaptive foreground **when** it fits the official splash icon mask without clipping. **Use when:** the launcher asset clips or fails the mask - supply a dedicated splash drawable per [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen).

Theme shape (replace names and colors with project resources):

```xml
<style name="Theme.App.Splash" parent="Theme.SplashScreen">
    <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
    <item name="windowSplashScreenBackground">@color/splash_background</item>
    <item name="postSplashScreenTheme">@style/Theme.App</item>
</style>
```

Compose apps call `setContent { }` on `ComponentActivity`; View-only apps call `setContentView(...)`. Theme, manifest, and `installSplashScreen()` stay the same. Full checklist and performance rules: `references/android-performance.md` → **App Startup & Initialization** → **Splash Screen**.

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

**SupportSQLite → driver** migration: [Migrate from SupportSQLite](https://developer.android.com/kotlin/multiplatform/room#migrate) (Android-relevant parts apply even in Android-only apps).

### Composite relation keys (Room 3.0.0-alpha05+)

`@Relation` and `@Junction` accept **array**-valued `parentColumns` and `entityColumns` for composite foreign keys. Regenerate with KSP after bumping the catalog `room3` pin.

### Invalidation and tests

- **`InvalidationTracker.Observer`** / **`addObserver`** are removed; use **`InvalidationTracker.createFlow`** ([release notes](https://developer.android.com/jetpack/androidx/releases/room3)).
- **Instrumented tests:** `androidx.room3:room3-testing`, **`MigrationTestHelper`** with a **`SQLiteDriver`**, **`SQLiteConnection`**, and **suspend** APIs - see [Test migrations](https://developer.android.com/training/data-storage/room/migrating-db-versions#test) and [`MigrationTestHelper`](https://developer.android.com/reference/kotlin/androidx/room3/testing/MigrationTestHelper). In-repo examples: `references/testing.md`.

### Room 2.x lifecycle (context only)

Room 2.x remains in **maintenance** (bugfixes / dependency updates) while Room 3 is the active line ([blog](https://android-developers.googleblog.com/2026/03/room-30-modernizing-room.html)). Plan upgrades on a branch; align **Kotlin**, **KSP**, and **sqlite** versions with [Room 3 releases](https://developer.android.com/jetpack/androidx/releases/room3).

## Android 17 (API 37) Migration

Install **Android SDK Platform 37** in the SDK Manager (distinct from platform-tools). `compileSdk = 37` without that platform package fails sync.

Set `compileSdk` / `targetSdk` to 37 in the version catalog. Pin `agp`, Gradle wrapper, `kotlin`, and `ksp` as **independently verified** pairs per [gradle-setup.md](gradle-setup.md#agp-version-pin-resolve-before-merge), [gradle-setup.md → Example tested stack](gradle-setup.md#example-tested-stack-re-verify-after-every-bump), and [dependencies.md](dependencies.md#kotlin-compose-compiler-compatibility). Gradle wrapper 9.5.x does **not** imply AGP 9.5.x; HTTP 404 on `com.android.tools.build:gradle:<version>` means that AGP coordinate is not published yet on `google()` - pick a lower published AGP that still supports API 37. Catalog `kotlin` and `ksp` need a supported combination; KSP patch numbers may differ from Kotlin patch numbers - resolve from Maven Central / KSP release notes, then run `./gradlew help`. Leave AGP built-in Kotlin enabled; do not flip `android.builtInKotlin=false` mid-migration without a full plugin plan ([gradle-setup.md → Built-in Kotlin (AGP 9)](gradle-setup.md#built-in-kotlin-agp-9)). If `compile*JavaWithJavac` fails with `MissingValueException`, isolate JaCoCo combined coverage wiring before bumping Kotlin ([android-code-coverage.md](android-code-coverage.md)). Align the Compose BOM per [dependencies.md](dependencies.md).

Apply each topic below in order; authoritative rules live in the linked references.

### 16 KB memory page size (Play and native code)

Google Play blocks new apps and updates to existing apps that target Android 15+ on 64-bit when packaged native libraries fail 16 KB page-size compatibility. Read [Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes) and [Prepare Play apps for 16 KB devices](https://android-developers.googleblog.com/2025/05/prepare-play-apps-for-devices-with-16kb-page-size.html) for deadlines, ELF rules, NDK/AGP defaults, packaging, and emulator images.

Required: treat every `*.so` under `arm64-v8a` and `x86_64` (CMake/ndk-build outputs, `jniLibs/`, prebuilts, game engines, SQL/ML/media SDKs).

Use when: a release APK or AAB contains `lib/` - run alignment verification on that artifact before upload.

Forbidden: skipping the audit on Kotlin-only app modules; transitive AARs still inject native libs.

Verification:

- Run APK Analyzer on the release build; inspect each `.so` Alignment column per the page-size guide.
- Run AOSP `check_elf_alignment.sh` on the release APK, or inspect extracted `lib/**/*.so` with `llvm-readelf` / `readelf` exactly as [ELF alignment checks](https://developer.android.com/guide/practices/page-sizes#elf-alignment) describe.
- Boot a 16 KB emulator image and execute the app's critical paths per [Test in a 16 KB environment](https://developer.android.com/guide/practices/page-sizes#test).

Build and supply chain:

- Bump NDK and AGP only through pairs already validated in [gradle-setup.md](gradle-setup.md) and [dependencies.md](dependencies.md); follow the page-size guide **Build** / **Compile** sections for linker flags and defaults on the active NDK line.
- Prebuilt `.so` files from vendors: upgrade the SDK, obtain a 16 KB-aligned artifact, or drop the dependency - relinking inside the app does not fix an opaque third-party binary.

### Launcher `Activity` soft input (IME baseline)

Set `android:windowSoftInputMode="adjustResize"` on the launcher `Activity` that hosts Compose even when no `TextField` exists yet; first text input on target SDK 37 otherwise hits IME inset footguns. Full rules: [compose-patterns.md → IME (soft keyboard) insets](compose-patterns.md#ime-soft-keyboard-insets).

### Cleartext traffic

At target SDK 37, cleartext defaults off unless a Network Security Config or manifest flag overrides it. Replace blanket `usesCleartextTraffic="true"` with domain-scoped NSC entries for dev and staging hosts. Full directives: [android-security.md → Network Security Configuration](android-security.md#network-security-configuration).

### Loopback (127.0.0.1)

Cross-process loopback sockets require the API 37 permission and pairing rules in [android-security.md → Loopback access (API 37)](android-security.md#loopback-access-api-37).

### Certificate Transparency

Default CT enforcement and per-domain opt-out live in [android-security.md → Certificate Transparency (API 37)](android-security.md#certificate-transparency-api-37).

### Background media playback

Route background audio and video through Media3 `MediaSessionService`, `mediaPlayback` foreground service type, and a `MediaSession` around a `Player`. Standalone `MediaPlayer`, `AudioTrack`, or raw `ExoPlayer` without a session breaks at target 37. Manifest and service skeleton: [android-media.md → Background media playback hardening (API 37)](android-media.md#background-media-playback-hardening-api-37).

### Large-screen orientation and resizability

`screenOrientation`, `resizableActivity="false"`, and aspect-ratio caps are ignored on `sw600dp+` displays at API 36+; API 37 keeps that rule and expects the app window to fill the display on those devices. Build `WindowSizeClass`-driven UIs instead of manifest locks. Games (`android:appCategory="game"`) follow platform carve-outs; confirm eligibility in [Android 17 migration](https://developer.android.com/about/versions/17/migration). In-repo layout rules: [compose-patterns.md → Adaptive Layouts (Mandatory on API 36+ for Large Screens)](compose-patterns.md#adaptive-layouts-mandatory-on-api-36-for-large-screens).

### IME after rotation

Target SDK 37 does not restore IME visibility across configuration changes by default. Wire `android:windowSoftInputMode` and runtime `WindowInsetsControllerCompat` per [compose-patterns.md → IME (soft keyboard) insets](compose-patterns.md#ime-soft-keyboard-insets).

### JVM unit tests without Robolectric

Pure ViewModel, coroutine, and JVM tests under `src/test/` that do not use `@RunWith(RobolectricTestRunner::class)` skip Robolectric pinning entirely.

### Robolectric JVM tests

Robolectric 4.16.x shadows top out at SDK 36 until a newer release adds SDK 37; pin `@Config(sdk = [Build.VERSION_CODES.BAKLAVA])` and run JVM tests on JDK 21 when using that shadow. Full checklist: [testing.md → Robolectric and SDK 37 (Android 17)](testing.md#robolectric-and-sdk-37-android-17).

### Espresso instrumented tests

Keep **androidx.test.espresso:espresso-core** on the catalog version (`3.7.0`); sync Gradle after the catalog bump. No separate Espresso migration path for API 37.

### Memory limiter (all apps on affected devices)

A subset of devices enforce per-app memory caps; exceeding the cap kills the process. Applies regardless of `targetSdk`.

Required for reproduction: use platform `am memory-limiter` commands on a supported image. Full behavior: [Behavior changes: all apps](https://developer.android.com/about/versions/17/behavior-changes-all).

```bash
adb shell am memory-limiter status
adb shell am memory-limiter manual <packageName> <limitMb>
adb shell am memory-limiter ignore <packageName>
```

Use when: investigating unexplained background kills or OOM on specific OEM builds without a reproducible leak.

Route diagnosis: [android-debugging.md → Process kill under memory caps](android-debugging.md#process-kill-under-memory-caps).

### Android 17 location privacy

Target SDK 37 tightens location access patterns (approximate-first flows, background justification, FGS types). Directive table and Compose contracts: [android-permissions.md → Android 17 location privacy](android-permissions.md#android-17-location-privacy).

### Explicit URI grants on shares

Attach `FLAG_GRANT_READ_URI_PERMISSION` or `FLAG_GRANT_WRITE_URI_PERMISSION` explicitly when putting `content` URIs on intents that do **not** receive implicit URI grants. Which actions get implicit grants vs explicit flags: [android-security.md → URI grants on outbound intents](android-security.md#uri-grants-on-outbound-intents).
