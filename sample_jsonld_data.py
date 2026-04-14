EXAMPLE_JSONLD_DOCUMENT = {
    "@context": {
        "schema": "https://schema.org/",
        "dpp": "https://example.org/dpp#",
    },
    "@graph": [
        {
            "@id": "dpp-001",
            "@type": "dpp:DPPInstance",

            # rule-based
            "operatingHours": {
                "@value": 120.0,
                "unitCode": "hours"
            },
            "cleaning_cycles": {
                "@value": 14.0,
                "unitCode": "count"
            },

            # similarity fallback
            "descale_event_count": {
                "@value": 3.0,
                "unitCode": "count"
            },
            "brew_cycle_total": {
                "@value": 560.0,
                "unitCode": "cycles"
            },

            # negative / unmapped
            "backupLink": {
                "@value": "https://example.org/dpp-backup/dpp-001"
            }
        },
        {
            "@id": "mat-001",
            "@type": "dpp:MaterialInstance",

            # rule-based
            "percentRecycled": {
                "@value": 35.0,
                "unitCode": "percent"
            },

            # similarity fallback
            "material_mass_grams": {
                "@value": 540.0,
                "unitCode": "gram"
            },
            "material_purity_percentage": {
                "@value": 92.5,
                "unitCode": "percentage"
            }
        },
        {
            "@id": "part-static-001",
            "@type": "dpp:PartStatic",

            # rule-based
            "componentWeightGRM": {
                "@value": 1800.0,
                "unitCode": "g"
            },

            # hard / likely unmapped for now
            "manufacturer_name": {
                "@value": "Acme Components"
            }
        },
        {
            "@id": "transport-001",
            "@type": "dpp:TransportStep",

            # rule-based
            "transportDistance": {
                "@value": 85.0,
                "unitCode": "km"
            },

            # similarity fallback
            "travel_distance_km": {
                "@value": 91.0,
                "unitCode": "kilometers"
            }
        },
        {
            "@id": "ghg-001",
            "@type": "dpp:GHGEmissionRecord",

            # rule-based
            "ghgEmissions": {
                "@value": 12.4,
                "unitCode": "kg_co2e"
            },

            # similarity fallback
            "carbon_emissions_kg_co2e": {
                "@value": 13.1,
                "unitCode": "kg co2e"
            }
        }
    ]
}