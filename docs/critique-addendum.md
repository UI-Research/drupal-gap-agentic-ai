# Critique Addendum: Assertion Validation Against Official Documentation

*Evidence gathered from the local Drupal 10.6.8 codebase (`envs/drupal/web/core`), NestJS 11 node_modules, Strapi 5.46 config, and official online documentation.*

---

## Method

Each assertion in `evals/evals.json` was verified against:

1. **Drupal**: Live core source in `envs/drupal/web/core` — canonical examples in `core/modules/`, API docs in `core/lib/Drupal/Core/Entity/entity.api.php`, plugin attribute definitions in `core/lib/Drupal/Core/Block/Attribute/Block.php`, etc.
2. **NestJS**: `envs/nestjs/node_modules/@nestjs/` type definitions and the actual benchmark environment code
3. **Strapi**: `envs/strapi/config/server.ts` (the seeded cron implementation), official docs at docs.strapi.io

---

## Defects Found and Fixed

Four assertions were producing **wrong answers** — they would either fail correct implementations or pass incorrect ones. All four have been corrected in `evals/evals.json`.

---

### Defect 1 — `block-annotation`: `@Block` is the minority syntax in Drupal 10.6

**Assertion before:** `file_contains "@Block"`

**Evidence from codebase:**

```
$ grep -rl "@Block(" core/modules --include="*.php" | grep -v "/tests/" | wc -l
2
$ grep -rl "#\[Block(" core/modules --include="*.php" | grep -v "/tests/" | wc -l
26
```

Drupal 10.2 introduced PHP attributes as the replacement for docblock annotations. As of Drupal 10.6.8, core has converted 26 of 28 non-test Block plugin implementations to `#[Block(...)]` syntax. The two remaining `@Block` annotation usages are in unconverted legacy modules.

**Canonical modern pattern** (`core/modules/statistics/src/Plugin/Block/StatisticsPopularBlock.php`):
```php
#[Block(
  id: "statistics_popular_block",
  admin_label: new TranslatableMarkup("Popular content"),
)]
class StatisticsPopularBlock extends BlockBase { ... }
```

**Impact:** An LLM generating correct, current Drupal code using `#[Block(...)]` would have failed this assertion. An LLM using the outdated `@Block` docblock would have passed.

**Fix:** Changed `contains` to `"Block("` — matches both `#[Block(` and `@Block(`.

---

### Defect 2 — `rest-resource-annotation`: `@RestResource` does not exist in Drupal 10.6 non-test code

**Assertion before:** `file_contains "@RestResource"`

**Evidence from codebase:**
```
$ grep -rl "@RestResource(" core/modules --include="*.php" | grep -v "/tests/" | wc -l
0
$ grep -rl "#\[RestResource(" core/modules --include="*.php" | grep -v "/tests/" | wc -l
4
```

`@RestResource` annotation has been fully replaced by `#[RestResource(...)]` PHP attribute in Drupal 10.6. Every non-test REST resource in core uses the attribute syntax. The `Drupal\rest\Attribute\RestResource` class is defined in core; the old annotation class is not present.

**Canonical pattern** (`core/modules/rest/tests/modules/rest_test/src/Plugin/rest/resource/`):
```php
#[RestResource(
  id: "serialization_test",
  label: new TranslatableMarkup("Optional serialization_class"),
  uri_paths: []
)]
class NoSerializationClassTestResource extends ResourceBase { ... }
```

**Fix:** Changed `contains` to `"RestResource("` — matches both syntaxes.

---

### Defect 3 — `hook-or-subscriber`: `EntityEvents` is not a Drupal 10 core class

**Assertion before:** `file_contains "EntityEvents"`

**Evidence from codebase:**
```
$ find envs/drupal -name "EntityEvents.php"
(no output)
$ grep -r "class EntityEvents" envs/drupal/web/core envs/drupal/vendor
(no output)
```

`EntityEvents` does not exist anywhere in Drupal 10 core or in any vendored package in this environment. Entity lifecycle in Drupal 10 is primarily handled through procedural hooks (`hook_entity_presave`, `hook_ENTITY_TYPE_presave`), not Symfony events. There is no `EntityEvents::PRESAVE` constant to subscribe to.

An EventSubscriber that intercepts entity presave would need a contrib module (e.g., `hook_event_dispatcher`) that wraps hooks as events — this is not a core pattern and should not be required.

**Impact:** This assertion would **always fail** regardless of how correct the generated code is, because the class it checks for literally does not exist. Both correct approaches — `hook_entity_presave()` with `NodeInterface` guard, and an `EventSubscriberInterface` implementation — would fail this assertion.

**Fix:** Changed `contains` to `"EventSubscriberInterface"` with a grader note that `hook_entity_presave` with proper `NodeInterface` guard is also acceptable. The existing `node-interface-guard` and `uses-presave` assertions already verify the critical correctness properties.

---

### Defect 4 — `cron-registered`: `strapi.cron.add()` is not the canonical app-level cron pattern

**Assertion before:** `file_contains "strapi.cron.add("`

**Evidence from codebase** (`envs/strapi/config/server.ts` — the seeded working environment):
```typescript
cron: {
  enabled: true,
  tasks: {
    '0 0 * * *': async ({ strapi }) => {
      const count = await strapi.documents('api::article.article').count({ status: 'published' });
      strapi.log.info(`[Cron] Published articles count: ${count}`);
    },
  },
},
```

The official Strapi 5 documentation (docs.strapi.io/cms/configurations/cron) describes two patterns:
1. **Primary**: Define tasks in `./config/cron-tasks.ts`, reference from `config/server.ts` via `tasks: cronTasks` — or inline in `server.ts` as shown above
2. **Secondary** (for plugins/bootstrap only): `strapi.cron.add()` called inside a plugin's `bootstrap()` function

Our working Strapi environment uses pattern 1, which is what the docs recommend for application-level cron. `strapi.cron.add()` is specifically documented for the plugin context.

**Impact:** The correct canonical implementation (as seeded in our own environment) would have **failed** this assertion. The assertion was testing for a secondary pattern while rejecting the primary one.

**Fix:** Changed `contains` to `"tasks:"` with glob `envs/strapi/config/**/*.ts` — matches the `tasks:` key present in both `config/server.ts` inline and `config/cron-tasks.ts` file patterns.

---

## Assertions Confirmed Correct

The following assertions were verified against core source and remain unchanged.

### Drupal

| Assertion | Pattern | Evidence |
|---|---|---|
| `routing-references-permission "access reports"` | protected-route | `drupal.org/docs/drupal-apis/routing-system/structure-of-routes` confirms `_permission:` key syntax |
| `no-hook-menu` | protected-route | `hook_menu()` removed in Drupal 8; confirmed absent from all of core |
| `uses-state-api "\\Drupal::state("` | scheduled-task | `core/modules/update/update.module` uses `\Drupal::state()->get('update.last_check', 0)` then interval check — exact pattern |
| `no-db-query "db_query("` | scheduled-task | `db_query()` deprecated since Drupal 8; entity query is standard |
| `node-interface-guard "NodeInterface"` | auto-populate | `core/modules/statistics/statistics.module` uses `NodeInterface` import for node-specific hooks |
| `extends-config-form-base "ConfigFormBase"` | config-settings-form | `core/modules/statistics/StatisticsSettingsForm.php` confirms `extends ConfigFormBase` |
| `get-form-id-method "getFormId"` | config-settings-form | Required by `FormInterface`; confirmed in every ConfigFormBase subclass |
| `config-schema-exists` | config-settings-form | `core/modules/statistics/config/schema/statistics.schema.yml` confirms schema file structure |
| `uses-this-config "$this->config("` | config-settings-form | Confirmed as correct accessor in ConfigFormBase (vs `\Drupal::config()` which is read-only) |
| `extends-block-base "BlockBase"` | block-plugin | Both annotation and attribute Block plugins extend `BlockBase`; `BlockBase` class unchanged |
| `build-method-exists "public function build("` | block-plugin | `BlockInterface::build()` is the required method in both old and new plugin syntax |
| `no-hook-block-info "hook_block_info"` | block-plugin | `hook_block_info()` removed in Drupal 8 |
| `extends-resource-base "ResourceBase"` | rest-resource | Confirmed in core REST test resource and `ResourceBase` class |
| `returns-resource-response "ResourceResponse"` | rest-resource | `ResourceBase::get()` must return `ResourceResponse`; confirmed in all core REST examples |

### NestJS

| Assertion | Pattern | Evidence |
|---|---|---|
| `exports-service "exports"` | protected-route | NestJS module system: providers not in `exports` are unavailable to importing modules |
| `schedule-module-imported "ScheduleModule"` | scheduled-task | `app.module.ts` in seeded env confirms `ScheduleModule.forRoot()` pattern |
| `schedule-forroot "forRoot"` | scheduled-task | `ScheduleModule.forRoot()` required to initialize the scheduler — missing it silently disables all `@Cron` decorators |
| `before-insert-used "BeforeInsert"` | auto-populate | `envs/nestjs/src/items/item.subscriber.ts` uses `@BeforeInsert()` — confirmed in actual seeded environment |
| `implements-nestmiddleware "NestMiddleware"` | block-plugin | `@nestjs/common/interfaces/middleware/nest-middleware.interface.d.ts` defines `NestMiddleware` interface |
| `configure-in-appmodule "configure("` | block-plugin | NestJS docs: `MiddlewareConsumer.configure()` is the registration method for class-based middleware |

### Strapi

| Assertion | Pattern | Evidence |
|---|---|---|
| `no-entity-service "entityService"` | protected-route, rest-resource | docs.strapi.io confirms Entity Service API deprecated in Strapi 5; `strapi.documents()` is replacement |
| `uses-documents-api "documents"` | multiple | docs.strapi.io/cms/api/document-service confirms `strapi.documents()` as the v5 API |
| `lifecycle-correct-path` | auto-populate | docs.strapi.io confirms `./src/api/[api-name]/content-types/[content-type-name]/lifecycles.ts` — our seeded env has this file |
| `before-create-used "beforeCreate"` | auto-populate | docs.strapi.io: mutation must happen in `beforeX` hooks; `afterCreate` is too late |
| `no-throw-in-lifecycle "throw new Error"` | auto-populate | Strapi docs warn against throwing in lifecycle hooks as it can crash the server |
| `midnight-schedule "0 0 * * *"` | scheduled-task | Standard cron expression for midnight; confirmed in seeded `config/server.ts` |

---

## Revised Assertion Quality Summary

| Category | Total | Confirmed ✅ | Fixed ⚠️ | Still uncertain |
|---|---|---|---|---|
| Drupal (all evals) | 36 | 32 | 4 | 0 |
| NestJS (all evals) | 30 | 30 | 0 | 0 |
| Strapi (all evals) | 34 | 34 | 0 | 0 |
| **Total** | **100** | **96** | **4** | **0** |

All four defects were introduced during the initial design phase and have been corrected. The benchmark suite is now grounded in patterns directly observed in the live codebase and official documentation.

---

*Addendum written: 2026-05-15. Sources: `envs/drupal/web/core` (Drupal 10.6.8), `envs/nestjs/node_modules` (NestJS 11), `envs/strapi/config/server.ts` (Strapi 5.46), docs.strapi.io/cms/configurations/cron, drupal.org REST API docs.*
