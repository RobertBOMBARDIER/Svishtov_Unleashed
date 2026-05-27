"""
Seed endpoint — inserts sample Svishtov attractions for development/demo.
Only available when APP_ENV=development.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.dependencies import get_db
from app.models.attraction import Attraction

router = APIRouter(prefix="/seed", tags=["seed"])

SAMPLE_ATTRACTIONS = [
    {
        "name": "Monumentul Aleko Konstantinov",
        "category": "monument",
        "latitude": 43.6189,
        "longitude": 25.3467,
        "address": "Piața Centrală, Svishtov",
        "lore_ro": "Aleko Konstantinov (1863–1897) a fost un scriitor și publicist bulgar, născut în Svishtov. Este cunoscut mai ales pentru romanul satiric 'Bai Ganyo', o capodoperă a literaturii bulgare care descrie tipul omului balcanic lipsit de cultură. Monumentul din centrul orașului îl comemorează pe acest fiu ilustru al Svishtovului, care a contribuit enorm la cultura și identitatea națională bulgară. Konstantinov a studiat dreptul la Sankt Petersburg și a lucrat ca avocat, dar pasiunea sa pentru literatură l-a transformat într-una dintre cele mai importante voci ale epocii sale.",
        "lore_en": "Aleko Konstantinov (1863–1897) was a Bulgarian writer and publicist born in Svishtov. He is best known for the satirical novel 'Bai Ganyo', a masterpiece of Bulgarian literature depicting the uncultured Balkan type. The monument in the city center commemorates this illustrious son of Svishtov, who contributed enormously to Bulgarian culture and national identity. Konstantinov studied law in Saint Petersburg and worked as a lawyer, but his passion for literature transformed him into one of the most important voices of his era.",
        "wheelchair_access": True,
        "audio_facilities": False,
        "protection_status": "national_monument",
        "european_significance": "Aleko Konstantinov reprezintă un simbol al identității culturale bulgare și al valorilor europene de libertate și umanism.",
    },
    {
        "name": "Fortăreața Romană Novae",
        "category": "monument",
        "latitude": 43.6312,
        "longitude": 25.3589,
        "address": "Novae, lângă Svishtov",
        "lore_ro": "Novae a fost un important castru roman și mai târziu oraș roman, situat pe malul drept al Dunării, lângă actualul Svishtov. Fondată în secolul I d.Hr., Novae a servit ca bază militară pentru Legiunea I Italica și a jucat un rol crucial în apărarea frontierei romane (limes) de-a lungul Dunării. Săpăturile arheologice au scos la iveală terme, bazilici, clădiri administrative și numeroase artefacte care ilustrează viața cotidiană romană. Novae este considerată unul dintre cele mai importante situri arheologice romane din Bulgaria.",
        "lore_en": "Novae was an important Roman legionary fortress and later Roman city, located on the right bank of the Danube near present-day Svishtov. Founded in the 1st century AD, Novae served as the base for the First Italic Legion and played a crucial role in defending the Roman frontier (limes) along the Danube. Archaeological excavations have uncovered baths, basilicas, administrative buildings, and numerous artifacts illustrating Roman daily life. Novae is considered one of the most important Roman archaeological sites in Bulgaria.",
        "wheelchair_access": False,
        "audio_facilities": False,
        "protection_status": "national_monument",
        "european_significance": "Novae face parte din patrimoniul roman comun al Europei și reprezintă o mărturie a prezenței romane la Dunăre.",
    },
    {
        "name": "Muzeul de Istorie Svishtov",
        "category": "museum",
        "latitude": 43.6178,
        "longitude": 25.3445,
        "address": "Str. Tsar Osvoboditel 20, Svishtov",
        "lore_ro": "Muzeul de Istorie din Svishtov găzduiește o colecție bogată de artefacte care acoperă istoria regiunii de la preistorie până în epoca modernă. Printre exponate se numără obiecte din epoca romană descoperite la Novae, arme și documente din perioada Renașterii Bulgare, precum și materiale legate de Războiul Ruso-Turc din 1877-1878, când Svishtov a fost primul oraș bulgar eliberat. Muzeul oferă vizitatorilor o perspectivă completă asupra evoluției culturale și istorice a acestui important centru urban dunărean.",
        "lore_en": "The History Museum of Svishtov houses a rich collection of artifacts covering the history of the region from prehistory to the modern era. Exhibits include Roman-era objects discovered at Novae, weapons and documents from the Bulgarian National Revival period, and materials related to the Russo-Turkish War of 1877-1878, when Svishtov was the first Bulgarian city to be liberated. The museum offers visitors a comprehensive perspective on the cultural and historical evolution of this important Danubian urban center.",
        "wheelchair_access": True,
        "audio_facilities": True,
        "protection_status": None,
        "european_significance": None,
    },
    {
        "name": "Parcul și Plaja Dunărea",
        "category": "natural",
        "latitude": 43.6234,
        "longitude": 25.3512,
        "address": "Faleza Dunării, Svishtov",
        "lore_ro": "Faleza Dunării din Svishtov oferă o priveliște spectaculoasă asupra celui mai mare fluviu al Europei. Parcul amenajat de-a lungul malului oferă spații de recreere, locuri de picnic și o plajă populară în sezonul estival. Dunărea reprezintă nu doar o frontieră naturală, ci și o arteră comercială și culturală care a modelat istoria Svishtovului de-a lungul mileniilor. De pe faleză se poate vedea malul românesc al fluviului, iar în zilele senine panorama este deosebit de impresionantă.",
        "lore_en": "The Danube embankment in Svishtov offers a spectacular view of Europe's largest river. The park along the riverbank provides recreational spaces, picnic areas, and a popular beach during the summer season. The Danube represents not only a natural border but also a commercial and cultural artery that has shaped Svishtov's history over millennia. From the embankment, the Romanian bank of the river is visible, and on clear days the panorama is particularly impressive.",
        "wheelchair_access": True,
        "audio_facilities": False,
        "protection_status": None,
        "european_significance": "Dunărea este desemnată coridor natural european și face parte din rețeaua Natura 2000.",
    },
    {
        "name": "Catedrala Sfânta Treime",
        "category": "church",
        "latitude": 43.6165,
        "longitude": 25.3438,
        "address": "Str. Sveta Troitsa 1, Svishtov",
        "lore_ro": "Catedrala Sfânta Treime este principalul lăcaș de cult ortodox din Svishtov, construită în stilul arhitecturii religioase bulgare din perioada Renașterii Naționale. Interiorul este decorat cu fresce valoroase și iconostase sculptate în lemn, reprezentând capodopere ale artei religioase bulgare din secolul al XIX-lea. Biserica a jucat un rol important în menținerea identității culturale și religioase a populației bulgare în perioada otomană și continuă să fie un centru spiritual activ al comunității locale.",
        "lore_en": "The Holy Trinity Cathedral is the main Orthodox place of worship in Svishtov, built in the style of Bulgarian religious architecture from the National Revival period. The interior is decorated with valuable frescoes and wood-carved iconostases, representing masterpieces of 19th-century Bulgarian religious art. The church played an important role in maintaining the cultural and religious identity of the Bulgarian population during the Ottoman period and continues to be an active spiritual center of the local community.",
        "wheelchair_access": False,
        "audio_facilities": False,
        "protection_status": "local_heritage",
        "european_significance": None,
    },
]


@router.post("/attractions", summary="Seed sample attractions (dev only)")
async def seed_attractions(db: AsyncSession = Depends(get_db)):
    """Insert sample Svishtov attractions. Only works in development mode."""
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=403, detail="Seed endpoint only available in development.")

    # Check if already seeded
    result = await db.execute(select(Attraction).limit(1))
    if result.scalar_one_or_none() is not None:
        return {"message": "Database already has attractions. Skipping seed.", "count": 0}

    created = []
    for data in SAMPLE_ATTRACTIONS:
        attraction = Attraction(
            id=str(uuid.uuid4()),
            name=data["name"],
            category=data["category"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            address=data["address"],
            lore_ro=data["lore_ro"],
            lore_en=data["lore_en"],
            wheelchair_access=data["wheelchair_access"],
            audio_facilities=data["audio_facilities"],
            protection_status=data.get("protection_status"),
            european_significance=data.get("european_significance"),
        )
        db.add(attraction)
        created.append(data["name"])

    return {"message": f"Seeded {len(created)} attractions.", "attractions": created}
