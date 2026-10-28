# FireFusion Web

FireFusion is a responsive web prototype for exploring satellite fire detections
from the MODIS and VIIRS sensor families. It presents map markers, daily
aggregates, cluster evidence, validation status, and methodology in a single
interactive interface.

> **Important:** This prototype is not a wildfire prediction or safety tool. It
> does not forecast fire spread, danger, or evacuation routes. The included
> dataset is illustrative demo data, not measured or live fire observations.

## Contents

- [Requirements](#requirements)
- [Run locally](#run-locally)
- [Available routes](#available-routes)
- [How the app is organized](#how-the-app-is-organized)
- [Demo data and limitations](#demo-data-and-limitations)
- [Checks](#checks)
- [Related documentation](#related-documentation)

## Requirements

- Node.js 20.9 or newer
- Bun 1.2.21, the package manager version specified by the repository

Install dependencies from the repository root:

```bash
bun install --frozen-lockfile
```

Do not install dependencies from this directory; the app is part of the
repository's Bun workspace.

## Run locally

From the repository root, start only the web workspace:

```bash
bun run dev --filter=web
```

Or start the app from this directory:

```bash
bun run dev
```

Open [http://localhost:3000](http://localhost:3000). Run the app through the
development server rather than opening the HTML prototype directly so the
responsive design and application routes load together.

To create and serve a production build from this directory:

```bash
bun run build
bun run start
```

## Available routes

| Route                   | Screen                                       |
| ----------------------- | -------------------------------------------- |
| `/`                     | Overview                                     |
| `/map`                  | Fire activity map                            |
| `/calendar`             | Burning activity calendar                    |
| `/evidence`             | Cluster evidence, choosing a default cluster |
| `/evidence/[clusterId]` | Cluster evidence for the specified cluster   |
| `/validation`           | Validation metrics and demo run control      |
| `/methods`              | Methods and limitations                      |
| `/seasonal`             | Redirects to `/calendar`                     |

The Next.js route pages set the initial view in the prototype's URL fragment.
Evidence routes also pass the selected cluster ID.

## How the app is organized

The web app is a Next.js App Router workspace. Most route pages are lightweight
wrappers that select a screen in the prototype:

- `app/` contains route pages, the root layout, and shared app-level styles.
- `components/layout/PrototypeFrame.tsx` embeds the prototype in a responsive
  iframe and maps application routes to prototype views.
- `public/resources/FireFusion_Desktop_Prototype.html` contains the responsive
  app design, interactions, and its illustrative demo values.
- `public/resources/FireFusion_Mobile_Prototype.html` is the standalone mobile
  design reference.
- `public/resources/FireFusion_Prototype_v14.html` is the earlier standalone
  prototype, which reads the fixture in `public/data/dummy-data.json`.
- `config/nav.ts` defines the outer application navigation.

The route pages and map, calendar, and cluster interactions are rendered in the
iframe; Next.js provides the app routes and embedding shell. The active design
contains illustrative sample values for layout and interaction only. It does
not load live observations or the separate v14 JSON fixture.

## Demo data and limitations

The active desktop prototype's embedded values and the separate JSON fixture
are demo-only and not measured. In particular:

- The desktop design's map, calendar, FRP, and confidence examples are
  illustrative UI fixtures, not measured observations. Event scores are shown as
  unavailable because they are not implemented.
- The v14 JSON fixture has map data only for **15 March 2026** and illustrative
  calendar samples.
- In v14, map `x` and `y` positions are placeholder percentages, not geographic
  coordinates.
- Validation results, seasonal anomaly percentiles, and real score components
  are not implemented. The validation button is a timed UI demo and performs no
  calculation.

Do not present these values as real observations. The full data-field
definitions, expected shapes, and implementation gaps are documented in the
[data contract](./public/resources/docs/DATA_CONTRACT.md).

## Checks

Run these workspace checks from `apps/web`:

```bash
bun run lint
bun run check-types
bun run build
```

There is no automated test script defined for this workspace. The
[smoke-test checklist](./public/resources/docs/SMOKE_TEST.md) applies to the
standalone v14 prototype; also verify the app routes and desktop/mobile
breakpoints when changing the active responsive design.

## Related documentation

- [Prototype instructions and feature notes](./public/resources/instructions.md)
- [Data contract and known gaps](./public/resources/docs/DATA_CONTRACT.md)
- [Prototype smoke-test checklist](./public/resources/docs/SMOKE_TEST.md)
