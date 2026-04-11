# sample_jsonld_data.py

EXAMPLE_JSONLD_DOCUMENT = {
    "@context": {
        "schema": "https://schema.org/",
        "dpp": "https://example.org/dpp#",
    },
    "@graph": [
        {
            "@id": "dpp-001",
            "@type": "schema:Product",
            "operatingHRS": {
                "@value": 120.0,
                "unitCode": "h"
            },
            "runtimeHours": {
                "@value": 121.5,
                "unitCode": "h"
            },
            "operationTimeHRS": {
                "@value": 122.0,
                "unitCode": "h"
            },
            "cleaningCount": {
                "@value": 14.0,
                "unitCode": "count"
            },
            "chalkCount": {
                "@value": 3.0,
                "unitCode": "count"
            },
            "brewingCount": {
                "@value": 560.0,
                "unitCode": "count"
            }
        },
        {
            "@id": "mat-001",
            "@type": "dpp:MaterialInstance",
            "weightGRM": {
                "@value": 540.0,
                "unitCode": "g"
            },
            "weightKG": {
                "@value": 0.54,
                "unitCode": "kg"
            },
            "percentRecycled": {
                "@value": 35.0,
                "unitCode": "%"
            },
            "recycledRatio": {
                "@value": 0.35,
                "unitCode": "ratio"
            },
            "purityLevel": {
                "@value": 92.5,
                "unitCode": "%"
            }
        },
        {
            "@id": "transport-001",
            "@type": "schema:TransferAction",
            "distanceKM": {
                "@value": 85.0,
                "unitCode": "km"
            },
            "routeLengthM": {
                "@value": 85000.0,
                "unitCode": "m"
            }
        },
        {
            "@id": "ghg-001",
            "@type": "dpp:GHGEmissionRecord",
            "emissions_kg_co2e": {
                "@value": 12.4,
                "unitCode": "kg_co2e"
            },
            "emissions_g_co2e": {
                "@value": 12400.0,
                "unitCode": "g_co2e"
            }
        },
        {
            "@id": "part-static-001",
            "@type": "dpp:PartStatic",
            "weightGRM": {
                "@value": 220.0,
                "unitCode": "g"
            }
        },
        {
            "@id": "part-instance-001",
            "@type": "dpp:PartInstance",
            "weightKG": {
                "@value": 0.22,
                "unitCode": "kg"
            }
        }
    ]
}