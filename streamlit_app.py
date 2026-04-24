akir-iao/
├── .gitignore
├── README.md
├── requirements.txt
├── packages.txt          # Dépendances système (optionnel)
├── app.py                # Point d'entrée Streamlit Cloud
├── config.py
├── clinical/
│   ├── __init__.py
│   ├── news2.py
│   ├── vitaux.py
│   ├── scores.py
│   ├── triage.py
│   ├── triage_handlers/
│   │   ├── __init__.py
│   │   ├── cardio.py
│   │   ├── neuro.py
│   │   ├── pediatrie.py
│   │   └── autres.py
│   └── pharmaco.py
├── persistence/
│   ├── __init__.py
│   ├── registry.py
│   └── audit.py
├── ui/
│   ├── __init__.py
│   ├── styles.py
│   └── components.py
└── tests/
    ├── __init__.py
    ├── test_news2.py
    ├── test_triage.py
    └── test_pharmaco.py