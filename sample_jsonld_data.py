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
            "percentRecycled": {
                "@value": 35.0,
                "unitCode": "%"
            },
            "purityLevel": {
                "@value": 92.5,
                "unitCode": "%"
            }
        },
        {
            "@id": "part-static-001",
            "@type": "dpp:PartStatic",
            "weightGRM": {
                "@value": 1800.0,
                "unitCode": "g"
            }
        },
        {
            "@id": "transport-001",
            "@type": "schema:TransferAction",
            "distanceKM": {
                "@value": 85.0,
                "unitCode": "km"
            }
        },
        {
            "@id": "ghg-001",
            "@type": "dpp:GHGEmissionRecord",
            "emissions_kg_co2e": {
                "@value": 12.4,
                "unitCode": "kg_co2e"
            }
        }
    ]
}