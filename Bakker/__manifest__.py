{
    "name": "Bakker",  # The name that will appear in the App list
    "version": "18.0.1.0.3",  # Version
    "application": True,  # This line says the module is an App, and not a module
    "depends": ["base"],  # dependencies
    "data": [
        "data/bakker_koeken_data.xml",
        "views/bakker_koeken_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    'license': 'LGPL-3',
}
