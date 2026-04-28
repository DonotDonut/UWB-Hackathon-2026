# UWB-Hackathon-2026
Operational guide and debugging work in progress, 
final result is in the frontend prototype branch.

# CrowdCue
**Know the crowd. Staff the moment.**

CrowdCue is an AI-powered staffing prediction tool that helps businesses near event venues anticipate demand surges and schedule staff proactively, before the crowd arrives, not after.

Built at **UWB HACKS 2026** · University of Washington Bothell · April 2026
Contributors: Tim Caole, Lily Aguirre, Campbell Hamilton, & Sarah Rosen

## The Problem
Businesses near stadiums, arenas, and event venues face unpredictable spikes in foot traffic. Without advance notice, managers understaff, employees burn out, customers wait impatiently, and the business loses revenue and reputation it can't easily recover.

There are currently **no prediction tools** purpose-built for the businesses sitting in the radius of these events.

## The Solution
CrowdCue pulls real-time data from public APIs (via Ticketmaster) to identify upcoming events near a target location, estimates crowd size and arrival patterns, and generates a recommended staffing schedule automatically.

A manager inputs their staff availability. CrowdCue does the rest.

## Features
- **Event-aware scheduling** — Integrates Ticketmaster and OpenStreetMap (Overpass) data to detect nearby events in real time
- **Location proximity modeling** — Uses GIS data to estimate crowd flow relative to a business's address
- **ML-powered prediction** — ECLAT association rule mining to identify staffing patterns tied to event types, size, and timing
- **Web-based interface** — No app download required; schedules generated in minutes
- **Minimal input required** — Only needs staff availability to produce a full recommendation

## Tech Stack
| Layer | Technology |
|---|---|
| Data Ingestion | Ticketmaster API, Turbo Overpass API |
| Geospatial | GIS database, location proximity engine |
| ML Model | ECLAT (association rule mining) |
| Backend | Python |
| Frontend | Web-based interface |

## Architecture Overview
```
Ticketmaster API ──┐
                   ├──▶ Event Aggregator ──▶ GIS Proximity Filter ──▶ ECLAT Model ──▶ Schedule Output
Overpass API ──────┘                                                        ▲
                                                                  Staff Availability Input
```

## Economic Context
CrowdCue was designed and validated around the **3rd Ave & Pike St corridor in Seattle, WA**:

- **$20.76/hr** Seattle minimum wage (Jan 2025) — razor-thin margins demand precision staffing
- **300+ major events** within one mile per year (Lumen Field, Climate Pledge Arena, etc.)
- **20M+ annual visitors** to the Pike Place / downtown core
- **FIFA World Cup 2026** — 6 matches at Lumen Field, expected to be the highest-traffic event series in Seattle's history
- Average restaurant margin: **~1.5%** — one bad staffing night can eliminate a day's profit

## Pitch Deck
📎 [CrowdCue Presentation.pdf](https://github.com/user-attachments/files/27147935/CrowdCue.Presentation.pdf)

## License
This project was created for hackathon purposes. All rights reserved by the team.
