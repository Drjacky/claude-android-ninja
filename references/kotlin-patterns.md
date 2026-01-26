# Kotlin Patterns & Best Practices

Concise Kotlin guidance for Android projects. Each item includes a short example so it is easy
to apply. If a topic is large, it lives in a dedicated reference and is linked here.

## Delegation (Composition over Inheritance)
Use delegation (`by`) to compose shared behavior instead of base classes. See:
`references/kotlin-delegation.md`.

## Prefer Read-Only Collection APIs
Expose `List`, `Set`, or `Map` from public APIs and keep mutable collections private. This keeps
mutation localized and makes state transitions explicit.

```kotlin
class AuthSessionStore {
    private val sessions = mutableMapOf<String, Session>()

    fun upsert(session: Session) {
        sessions[session.id] = session
    }

    fun snapshot(): Map<String, Session> = sessions
}
```

## Use Explicit State Transitions for Collections
Model collection changes as pure transformations so updates are predictable and testable.
This also makes it clear what “state machine” step is happening on each event.

```kotlin
sealed interface SessionEvent {
    data class Added(val session: Session) : SessionEvent
    data class Removed(val id: String) : SessionEvent
}

fun reduceSessions(
    current: List<Session>,
    event: SessionEvent
): List<Session> = when (event) {
    is SessionEvent.Added -> current + event.session
    is SessionEvent.Removed -> current.filterNot { it.id == event.id }
}
```

## Persistent Collections for State
When you store lists in Compose or ViewModel state, prefer persistent collections for structural
sharing and stable updates. This is covered in
`references/compose-patterns.md` → “Stability, Immutability, and Persistent Collections”.
