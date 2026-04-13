EXAMPLE_JSONLD_DOCUMENT = {
    "@context": {
        "schema": "https://schema.org/",
        "dpp": "https://example.org/dpp#",
    },
    "@graph": [
        {
            "@id": "dpp-001",
            "@type": "dpp:DPPInstance",
            "runtime_hours_total": {
                "@value": 120.0,
                "unitCode": "hours"
            },
            "cleaning_events_total": {
                "@value": 14.0,
                "unitCode": "events"
            },
            "descale_event_count": {
                "@value": 3.0,
                "unitCode": "count"
            },
            "brew_cycle_total": {
                "@value": 560.0,
                "unitCode": "cycles"
            }
        },
        {
            "@id": "mat-001",
            "@type": "dpp:MaterialInstance",
            "material_mass_grams": {
                "@value": 540.0,
                "unitCode": "gram"
            },
            "recycled_material_share": {
                "@value": 35.0,
                "unitCode": "percent"
            },
            "material_purity_percentage": {
                "@value": 92.5,
                "unitCode": "percentage"
            }
        },
        {
            "@id": "part-static-001",
            "@type": "dpp:PartStatic",
            "component_mass_grams": {
                "@value": 1800.0,
                "unitCode": "g"
            }
        },
        {
            "@id": "transport-001",
            "@type": "dpp:TransportStep",
            "travel_distance_km": {
                "@value": 85.0,
                "unitCode": "kilometers"
            }
        },
        {
            "@id": "ghg-001",
            "@type": "dpp:GHGEmissionRecord",
            "carbon_emissions_kg_co2e": {
                "@value": 12.4,
                "unitCode": "kg co2e"
            }
        }
    ]
}