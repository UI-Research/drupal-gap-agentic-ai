# Drupal 10 Skill Context

Actionable reference for LLM code generation targeting Drupal 10. Load this to avoid common structural mistakes.

## Routing & Permissions

- Routes: defined in `mymodule.routing.yml` — `hook_menu()` does NOT exist in Drupal 10
- Custom permissions MUST be defined in `mymodule.permissions.yml` — referencing an undefined permission in `_permission` silently denies all access
- Permission machine names use **lowercase with spaces**: `access reports` not `access_reports`
- Route format:

```yaml
mymodule.route_name:
  path: '/path'
  defaults:
    _controller: '\Drupal\mymodule\Controller\MyController::method'
  requirements:
    _permission: 'my permission'
```

## Services & Dependency Injection

- Services declared in `mymodule.services.yml` with `class` and `arguments`
- Use **constructor injection**, never `\Drupal::service()` inside classes
- Service naming convention: `mymodule.service_name`
- Arguments reference other services with `@service.name` or use `'@entity_type.manager'`

```yaml
services:
  mymodule.my_service:
    class: Drupal\mymodule\Service\MyService
    arguments: ['@entity_type.manager', '@logger.factory']
```

## Event Subscribers vs Hooks

- EventSubscribers with service tag `event_subscriber` are preferred over procedural hooks
- `hook_entity_presave()` works but **always needs an entity type guard**:
  ```php
  if (!$entity instanceof \Drupal\node\NodeInterface) {
    return;
  }
  ```
- For entity lifecycle: use `hook_entity_presave` / `hook_entity_insert` with type checks, or EventSubscriber pattern
- presave = can modify entity before write; insert/update = entity already saved (too late to mutate)

## Cron & Scheduled Tasks

- `hook_cron()` fires on cron cadence, NOT at a specific time — it **cannot** schedule "daily at midnight"
- For time-specific scheduling: use QueueWorker with `@QueueWorker` annotation + state API for last-run tracking, or the Scheduler module
- Long-running tasks in `hook_cron()` block ALL other cron tasks — use Queue API instead
- Queue workers: plugins with `@QueueWorker` annotation, processed via cron queue runner
- Track last execution with `\Drupal::state()->get('mymodule.last_run')` and compare against desired interval

## Config Export

- Config MUST be exported via `drush cex` (config export), never hand-written
- The config export diff is ground truth — generated config must produce zero structural diff against Drupal's own export
- Config entity YAML lives in `config/install/` or `config/optional/` within the module
- `config/install/` = installed when module is enabled
- `config/optional/` = installed only if dependencies are met

## Module Structure

```
modules/custom/mymodule/
  mymodule.info.yml          # Required: name, type, core_version_requirement
  mymodule.module            # Optional: procedural hooks
  mymodule.routing.yml       # Routes
  mymodule.permissions.yml   # Permissions
  mymodule.services.yml      # Service definitions
  src/
    Controller/              # Route controllers
    EventSubscriber/         # Event subscribers (tagged services)
    Plugin/                  # Plugin classes (QueueWorker, Block, etc.)
    Service/                 # Service classes
  config/
    install/                 # Default config installed with module
    optional/               # Config installed only if dependencies met
```

### Minimum info.yml

```yaml
name: 'My Module'
type: module
description: 'Description here'
core_version_requirement: ^10
package: Custom
```

## Common LLM Mistakes to Avoid

1. **Using `hook_menu()`** — does not exist in Drupal 10 (removed in Drupal 8)
2. **Referencing permissions not defined in `permissions.yml`** — silently fails, all access denied
3. **Using `\Drupal::service()` inside a class** — use constructor injection via services.yml
4. **Putting time-specific logic in `hook_cron()`** — cron has no guaranteed schedule; use state API + interval check
5. **Writing config YAML by hand** — export from Drupal; hand-written config has wrong UUIDs/structure
6. **Missing entity type guards in entity hooks** — hook fires on ALL entity types without a guard
7. **Forgetting `.info.yml`** — module won't be discovered by Drupal at all
8. **Using `$entity->id()` without null check on new entities** — ID is null before first save
9. **Placing PHP classes outside `src/`** — PSR-4 autoloading requires `src/` directory
10. **Using deprecated `db_query()`** — use entity queries (`\Drupal::entityQuery()`) or injected database service
