# Kotlin Delegation (Composition over Inheritance)

Use Kotlin's class delegation (`by`) to share behavior across ViewModels and classes without relying on base classes.
This keeps responsibilities explicit, improves testability, and avoids deep inheritance chains.

## Why Delegation in Android

- **Avoid base class bloat**: Split cross-cutting concerns (logging, validation, feature flags) into focused interfaces.
- **Swap implementations easily**: Delegates are injected, so tests can replace them with fakes.
- **Keep ViewModels lean**: Behavior is composed instead of inherited.

## When to Use Delegation

- Shared behavior across multiple ViewModels or classes
- Behavior not tied to Android framework inheritance requirements
- Logic that benefits from clear interfaces and DI (e.g., validators, analytics, feature flags)

## When Not to Use It

- Single-use logic with no reuse
- Cases where delegation adds indirection without value
- Framework-required inheritance (e.g., `Activity`, `Application`)

## Basic Pattern

```kotlin
interface Logger {
    fun log(message: String)
}

class ConsoleLogger : Logger {
    override fun log(message: String) {
        println("LOG: $message")
    }
}

class ExampleViewModel(
    private val savedStateHandle: SavedStateHandle,
    logger: Logger
) : ViewModel(), Logger by logger {
    fun runAction() {
        log("Action started")
    }
}
```

## ViewModel Delegation Pattern

```kotlin
interface FormValidator {
    fun validateEmail(email: String): String?
    fun validatePassword(password: String): String?
}

class DefaultFormValidator @Inject constructor() : FormValidator {
    override fun validateEmail(email: String): String? =
        if (email.contains("@")) null else "Invalid email"

    override fun validatePassword(password: String): String? =
        if (password.length >= 8) null else "Password too short"
}

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val savedStateHandle: SavedStateHandle,
    validator: FormValidator
) : ViewModel(), FormValidator by validator {

    fun onEmailChanged(email: String) {
        val error = validateEmail(email)
        // Update state with validation result
    }
}
```

## Best Practices

- Delegate **interfaces**, not concrete classes.
- Keep delegated interfaces **small** and focused.
- Prefer DI to construct delegates; avoid creating them manually.
- If the delegate needs coroutines, pass required scope(s) explicitly.

## Related References

- Use with ViewModel patterns in `references/compose-patterns.md`.
- For permissions behavior, see `references/android-permissions.md`.

## Sources

- https://kotlinlang.org/docs/delegation.html