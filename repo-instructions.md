# 📱 Flutter Team Workflow & Repo Rules

To keep the Flutter project stable and avoid merge conflicts in `pubspec.yaml` or generated files, follow these rules:

### 📂 Folder Territory
- **Logic Lead:** Works in `/backend` (Logic, BLoCs/Controllers, Services).
- **Frontend Team:** Works in `/frontend/lib/ui` or `/frontend/lib/screens`.
- **Data Team:** Works in `/data_layer` (Repositories, Models, API Providers).

### 🛠 Flutter Specifics
1. **Adding Dependencies:** If you add a package to `pubspec.yaml`, notify the team immediately. 
2. **After Pulling:** Every time you `git pull origin main`, run:
   `cd frontend && flutter pub get`
3. **Generated Files:** Never manually edit files ending in `.g.dart` or `.freezed.dart`.

### 🌿 Branching Strategy
- **NO PUSHING TO MAIN.**
- Use feature branches: `git checkout -b feature/ui-login-page`.
- Open a Pull Request (PR) and get a "Thumbs Up" before merging.

### 🚀 Daily Routine
1. `git pull origin main`
2. `flutter pub get`
3. Start coding.
