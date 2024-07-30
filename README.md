# HealthTourismHub-HTontology

This repository contains the Health Tourism (HT) ontology, designed to support applications that integrate healthcare and tourism data for personalized user experiences.
HealthTourismHub is a platform that exploits the strengths of this ontology to offer a complete experience for users seeking HT packages.



## HT ontology


### Using the Ontology

1. The complete ontology is located in the `health_tourism_ont.owl` file inside the `data` folder within the `hth_app` directory.

2. Navigate to the `data` folder and download or copy the `health_tourism_ont.owl` file.

3. You can open an ontology management tool such as Protégé to incorporate the `health_tourism_ont.owl` file into your project workspace.

4. You may utilize a reasoner like HermiT to check for consistency and infer new knowledge based on the ontology's axioms and rules.


### Main top-level classes

| Class | Description |
|---|---|
| Provider | Categorizes entities that offer HT services |
| MedicalSpecialty | Categorizes fields within medicine |
| MedicalService | Categorizes medical treatments and procedures |
| Activity | Actions or experiences during a travel |
| Place | Categorizes a wide range of locations and landscapes |
| Amenity | Amenities offered by accommodation providers entities |
| Room | Room entities that are offered by accommodation providers |
| AccommodationFeature | Categorizes a range of features within an accommodation |

**This ontology specifically includes individuals created exclusively for the HTH application, focusing on entities related to Greece. It includes medical and accommodation providers, as well as detailed location information and tourism activitied that are designed to support the application’s needs.**

### Using the Ontology Handlers

The `ontology_handlers` folder contains important resources and tools for working with the ontology.

1. **sparql_queries.py**
   - Includes code for connecting to the [AllegroGraph](https://franz.com/agraph/support/documentation/6.4.0/python/api.html) host.
   - Contains SPARQL queries.
   - These queries are executed using the AllegoGraph host.

3. **add_to_ontology.py**
   - Contains code for adding data from the app to the ontology via the AllegoGraph host.


## HTH application

### Using the application

1. Clone the repository to your local machine


```bash
   git clone https://github.com/eHealthITI/HealthTourismHub-HTontology.git
   cd HealthTourismHub-HTontology
```


2. If you are using Docker to run the application, ensure you have Docker installed. Then, build and start the Docker containers:

```bash
docker-compose up --build
```

> [!IMPORTANT]  
> If you use the HT ontology in your work or project, please ensure to cite the following paper: [An Ontology-Based Booking Application for Personalized Packages in the Health Tourism Industry](https://www.mdpi.com/2071-1050/16/15/6505)

