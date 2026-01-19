# Android Development

Create production-quality Android applications following Google's official architecture guidance and [NowInAndroid](https://github.com/android/nowinandroid) best practices.
Use when building Android apps with Kotlin, Jetpack Compose, MVVM architecture, Hilt dependency injection, Room database, or Android multi-module projects.
Triggers on requests to create Android projects, screens, ViewModels, repositories, feature modules, or when asked about Android architecture patterns.


## Quick Reference

| Task                                                 | Reference File                                        |
|------------------------------------------------------|-------------------------------------------------------|
| Project structure & modules                          | [modularization.md](references/modularization.md)     |
| Architecture layers (Presentation, Domain, Data, UI) | [architecture.md](references/architecture.md)         |
| Jetpack Compose patterns                             | [compose-patterns.md](references/compose-patterns.md) |
| Gradle & build configuration                         | [gradle-setup.md](references/gradle-setup.md)         |
| Testing approach                                     | [testing.md](references/testing.md)                   |
| Multi-module dependencies                            | [dependencies.md](references/dependencies.md)         |

## Workflow Decision Tree

**Creating a new project?**
→ Read [modularization.md](references/modularization.md) for project structure
→ Use templates in `templates/`
→ Set up **app module** for navigation and DI setup
→ Configure **feature modules** and **core modules**

**Adding a new feature?**
→ Create **feature module** following naming convention `feature-[name]`
→ Implement **Presentation Layer** in feature module
→ Follow dependency flow: Feature → Core/Domain → Core/Data
→ Add navigation from **app module**

**Building UI screens?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Create Screen + ViewModel + UiState in **feature module**
→ Use shared components from `core/ui` when possible

**Setting up data layer?**
→ Read data layer section in [architecture.md](references/architecture.md)
→ Create Repository interfaces in `core/domain`
→ Implement Repository in `core/data`
→ Create DataSource + DAO in `core/data`

**Setting up navigation?**
→ Configure navigation graph in **app module**
→ Use feature module navigation destinations
→ Handle deep links and navigation arguments