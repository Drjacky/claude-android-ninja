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
→ Start with `templates/settings.gradle.kts.template` for settings and module includes  
→ Start with `templates/libs.versions.toml.template` for the version catalog  
→ Read [modularization.md](references/modularization.md) for structure and module types  
→ Use [gradle-setup.md](references/gradle-setup.md) for build files and build logic  

**Configuring Gradle/build files?**
→ Use [gradle-setup.md](references/gradle-setup.md) for module `build.gradle.kts` patterns  
→ Keep convention plugins and build logic in `build-logic/` as described in [gradle-setup.md](references/gradle-setup.md)  

**Adding or updating dependencies?**
→ Follow [dependencies.md](references/dependencies.md)  
→ Update `templates/libs.versions.toml.template` if the dependency is missing  

**Adding a new feature/module?**
→ Follow module naming in [modularization.md](references/modularization.md)  
→ Implement Presentation in the feature module  
→ Follow dependency flow: Feature → Core/Domain → Core/Data

**Building UI screens/components?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Create Screen + ViewModel + UiState in the feature module  
→ Use shared components from `core/ui` when possible

**Setting up data/domain layers?**
→ Read [architecture.md](references/architecture.md)  
→ Create Repository interfaces in `core/domain`
→ Implement Repository in `core/data`
→ Create DataSource + DAO in `core/data`

**Setting up navigation?**
→ Follow Navigation Coordination in [modularization.md](references/modularization.md)  
→ Configure navigation graph in the app module  
→ Use feature navigation destinations and navigator interfaces  

**Adding tests?**
→ Use [testing.md](references/testing.md) for patterns and examples  
→ Keep test doubles in `core/testing`  