# -*- coding: utf-8 -*-
"""Build candidates.csv and per-batch lists from the curated candidate table.
Run with PYTHONUTF8=1 from the work/ directory."""
import csv, os
from collections import Counter

scr = list(csv.DictReader(open("skiresort_scrape.csv", encoding="utf-8")))

def find(sub):
    sub = sub.lower()
    for r in scr:
        if sub in r['name'].replace('​', '').lower():
            return r['url']
    return ''

# batch | resort_name | local_name | country | region | ski_area | inclusion_basis | road_head_hint | skiresort match | notes
C = """
FR1|Courchevel||FR|Savoie|3 Vallées|km≥60 (3 Vallées 600 km)||Les 3 Vall|Villages 1850/1650/1550/Le Praz = one row
FR1|Méribel||FR|Savoie|3 Vallées|km≥60||Les 3 Vall|Incl. Méribel-Mottaret
FR1|Les Menuires||FR|Savoie|3 Vallées|km≥60||Les 3 Vall|
FR1|Val Thorens||FR|Savoie|3 Vallées|km≥60; glacier (Péclet); alt 3230; FWT Val Thorens Pro 2025/26||Les 3 Vall|
FR1|Saint-Martin-de-Belleville||FR|Savoie|3 Vallées|km≥60||Les 3 Vall|
FR1|Orelle||FR|Savoie|3 Vallées|km≥60; alt (Cime Caron 3200)||Les 3 Vall|Maurienne-side gateway to Val Thorens
FR1|Tignes||FR|Savoie|Tignes–Val d'Isère (Espace Killy)|km≥60; glacier (Grande Motte); alt 3456||Tignes/Val d|Grande Motte glacier: check autumn opening
FR1|Val d'Isère||FR|Savoie|Tignes–Val d'Isère (Espace Killy)|km≥60; glacier (Pissaillas); alt||Tignes/Val d|
FR1|La Plagne||FR|Savoie|Paradiski|km≥60; glacier (Bellecôte – verify lifts); alt 3250||La Plagne|Villages incl. Montchavin, Champagny = one row
FR1|Les Arcs||FR|Savoie|Paradiski|km≥60; alt (Aiguille Rouge 3226); FWQ history||Les Arcs|
FR1|Peisey-Vallandry||FR|Savoie|Paradiski|km≥60||Les Arcs|
FR1|La Rosière||FR|Savoie|Espace San Bernardo|km≥60; alt 2800||Espace San Bernardo|Linked to La Thuile IT via Petit-St-Bernard (pass road closed in winter)
FR1|Sainte-Foy-Tarentaise||FR|Savoie|Sainte-Foy-Tarentaise|freeride destination in guidebooks (criterion 3)|||Small area; include for freeride reputation
FR1|Arêches-Beaufort||FR|Savoie|Arêches-Beaufort|ski-touring destination (Pierra Menta) (criterion 3)|||
FR1|Valmorel||FR|Savoie|Le Grand Domaine|km≥60||Le Grand Domaine|
FR1|Saint-François-Longchamp||FR|Savoie|Le Grand Domaine|km≥60||Le Grand Domaine|
FR1|Les Saisies||FR|Savoie|Espace Diamant|km≥60||Espace Diamant|Crest-Voland/Cohennoz and Flumet noted as villages, not rows
FR1|Notre-Dame-de-Bellecombe||FR|Savoie|Espace Diamant|km≥60||Espace Diamant|
FR1|Praz-sur-Arly||FR|Haute-Savoie|Espace Diamant|km≥60||Espace Diamant|
FR2|Le Corbier||FR|Savoie|Les Sybelles|km≥60||Les Sybelles|
FR2|La Toussuire||FR|Savoie|Les Sybelles|km≥60||Les Sybelles|
FR2|Saint-Sorlin-d'Arves||FR|Savoie|Les Sybelles|km≥60||Les Sybelles|
FR2|Saint-Jean-d'Arves||FR|Savoie|Les Sybelles|km≥60||Les Sybelles|
FR2|Valloire||FR|Savoie|Galibier-Thabor|km≥60||Galibier Thabor|Col du Galibier closed in winter
FR2|Valmeinier||FR|Savoie|Galibier-Thabor|km≥60||Galibier Thabor|
FR2|Val Cenis||FR|Savoie|Val Cenis (Haute Maurienne Vanoise)|km≥60; alt 2800||Val Cenis|Lanslevillard/Lanslebourg/Termignon = one row; Mont-Cenis pass closed in winter
FR2|Valfréjus||FR|Savoie|Valfréjus|km≥60||Valfr|Fréjus tunnel exit
FR2|La Norma||FR|Savoie|La Norma|km≥60||La Norma|
FR2|Les Karellis||FR|Savoie|Les Karellis|km≥60||Les Karellis|
FR2|Bonneval-sur-Arc||FR|Savoie|Bonneval-sur-Arc|alt 2947; touring hub|||Col de l'Iseran closed in winter
FR2|Alpe d'Huez||FR|Isère|Alpe d'Huez Grand Domaine|km≥60; glacier (Sarenne/Pic Blanc); alt 3330||Alpe d'Huez|Auris, Villard-Reculas noted as villages
FR2|Vaujany||FR|Isère|Alpe d'Huez Grand Domaine|km≥60||Alpe d'Huez|
FR2|Oz-en-Oisans||FR|Isère|Alpe d'Huez Grand Domaine|km≥60||Alpe d'Huez|
FR2|Les 2 Alpes||FR|Isère|Les 2 Alpes|km≥60; glacier; alt 3568||Les 2 Alpes|Glacier autumn opening; check 2026/27 dates
FR2|Les 7 Laux||FR|Isère|Les 7 Laux|km≥60||Les 7 Laux|Prapoutel/Pipay/Le Pleynet = one row
FR2|Chamrousse||FR|Isère|Chamrousse|km≥60||Chamrousse|
FR2|Villard-de-Lans–Corrençon||FR|Isère|Espace Villard-Corrençon (Vercors)|km≥60||Espace Villard|Vercors, Isère
FR3|Chamonix||FR|Haute-Savoie|Chamonix Mont-Blanc (Brévent-Flégère, Grands Montets, Balme, Aiguille du Midi)|glacier (Vallée Blanche, Grands Montets); alt 3842; FWT venue||Aiguille du Midi|Argentière/Le Tour = villages of Chamonix row. Check new Grands Montets lifts status
FR3|Megève||FR|Haute-Savoie|Evasion Mont-Blanc|km≥60||Meg|
FR3|Saint-Gervais-les-Bains||FR|Haute-Savoie|Evasion Mont-Blanc|km≥60||Meg|Incl. Saint-Nicolas-de-Véroce, Le Bettex
FR3|Combloux||FR|Haute-Savoie|Les Portes du Mont-Blanc / Evasion Mont-Blanc|km≥60 (Portes du Mont-Blanc 85 km)||Portes du Mont-Blanc|La Giettaz noted as village
FR3|Les Contamines-Montjoie||FR|Haute-Savoie|Les Contamines-Hauteluce (Evasion Mont-Blanc pass)|km≥60||Les Contamines|
FR3|La Clusaz||FR|Haute-Savoie|La Clusaz–Manigod|km≥60; FWQ history (Balme)||La Clusaz|Manigod on same local pass
FR3|Le Grand-Bornand||FR|Haute-Savoie|Le Grand-Bornand|km≥60||Le Grand Bornand|
FR3|Flaine||FR|Haute-Savoie|Le Grand Massif|km≥60||Le Grand Massif|
FR3|Les Carroz||FR|Haute-Savoie|Le Grand Massif|km≥60||Le Grand Massif|Les Carroz d'Arâches
FR3|Samoëns||FR|Haute-Savoie|Le Grand Massif|km≥60||Le Grand Massif|Sixt-Fer-à-Cheval noted as village
FR3|Morillon||FR|Haute-Savoie|Le Grand Massif|km≥60||Le Grand Massif|
FR3|Morzine||FR|Haute-Savoie|Portes du Soleil|km≥60||Portes du Soleil|
FR3|Avoriaz||FR|Haute-Savoie|Portes du Soleil|km≥60||Portes du Soleil|Car-free village; parking at entrance – check road head convention
FR3|Les Gets||FR|Haute-Savoie|Portes du Soleil|km≥60||Portes du Soleil|
FR3|Châtel||FR|Haute-Savoie|Portes du Soleil|km≥60||Portes du Soleil|La Chapelle-d'Abondance noted as village
FR3|Praz de Lys–Sommand||FR|Haute-Savoie|Praz de Lys–Sommand|km≥60||Praz de Lys|
FR4|Serre Chevalier||FR|Hautes-Alpes|Serre Chevalier Vallée|km≥60; alt 2800||Serre Chevalier|Briançon/Chantemerle/Villeneuve/Monêtier = one row
FR4|Montgenèvre||FR|Hautes-Alpes|Via Lattea (Vialattea)|km≥60||Via Lattea|Local Montgenèvre pass vs Vialattea international
FR4|Vars||FR|Hautes-Alpes|La Forêt Blanche (Vars–Risoul)|km≥60; FWQ history||Vars/Risoul|Col de Vars usually open in winter (check)
FR4|Risoul||FR|Hautes-Alpes|La Forêt Blanche (Vars–Risoul)|km≥60||Vars/Risoul|
FR4|Les Orres||FR|Hautes-Alpes|Les Orres|km≥60||Les Orres|
FR4|Orcières Merlette||FR|Hautes-Alpes|Orcières Merlette 1850|km≥60||Orci|
FR4|Puy-Saint-Vincent||FR|Hautes-Alpes|Puy-Saint-Vincent|km≥60||Puy-Saint-Vincent|
FR4|Le Dévoluy||FR|Hautes-Alpes|Le Dévoluy (Superdévoluy–La Joue du Loup)|km≥60||voluy|Two bases marketed as one destination
FR4|La Grave||FR|Hautes-Alpes|La Grave–La Meije|alt 3550; world-class freeride (criterion 3/4)||La Grave|Off-piste only; Col du Lautaret usually open (check)
FR4|Molines-en-Queyras–Saint-Véran||FR|Hautes-Alpes|Queyras|alt 2800 (verify)||Molines|Col Agnel/Izoard closed; access via Guillestre
FR4|Pra Loup||FR|Alpes-de-Haute-Provence|Espace Lumière|km≥60||Espace Lumi|
FR4|Val d'Allos–La Foux||FR|Alpes-de-Haute-Provence|Espace Lumière|km≥60||Espace Lumi|Col d'Allos closed in winter
FR4|Le Sauze–Super Sauze||FR|Alpes-de-Haute-Provence|Le Sauze|km≥60 (65 km)||Super Sauze|
FR4|Auron||FR|Alpes-Maritimes|Auron (Stations du Mercantour)|km≥60||Auron|
FR4|Isola 2000||FR|Alpes-Maritimes|Isola 2000 (Stations du Mercantour)|km≥60||Isola 2000|Col de la Lombarde closed in winter
FR4|Valberg||FR|Alpes-Maritimes|Valberg–Beuil|km≥60||Valberg|
IT1|Sestriere||IT|Turin, Piedmont|Via Lattea (Vialattea)|km≥60||Via Lattea|Pragelato noted as linked village
IT1|Sauze d'Oulx||IT|Turin, Piedmont|Via Lattea (Vialattea)|km≥60||Via Lattea|
IT1|Cesana–Sansicario||IT|Turin, Piedmont|Via Lattea (Vialattea)|km≥60||Via Lattea|
IT1|Claviere||IT|Turin, Piedmont|Via Lattea (Vialattea)|km≥60||Via Lattea|
IT1|Bardonecchia||IT|Turin, Piedmont|Bardonecchia|km≥60; alt 2800||Bardonecchia|
IT1|Alagna Valsesia||IT|Vercelli, Piedmont|Monterosa Ski|km≥60; glacier (Indren); alt 3275; FWQ/freeride mecca||Monterosa|
IT1|Prato Nevoso – Mondolè Ski||IT|Cuneo, Piedmont|Mondolè Ski (Prato Nevoso–Artesina–Frabosa)|km≥60 (105 km)||Mondol|Ligurian Alps; one row for Mondolè
IT1|Macugnaga||IT|Verbano-Cusio-Ossola, Piedmont|Macugnaga (Monte Moro)|alt 2900; glacier per skiresort.com (verify)||Macugnaga|Check current lift operation
IT1|Cervinia|Breuil-Cervinia|IT|Aosta, Valle d'Aosta|Matterhorn Ski Paradise (Zermatt–Cervinia–Valtournenche)|km≥60; glacier (Plateau Rosa); alt 3480||Zermatt/Breuil|Valtournenche on same local pass; autumn glacier opening
IT1|Courmayeur||IT|Aosta, Valle d'Aosta|Courmayeur Mont Blanc|km≥60? (approx 100 km incl. skyway?) ; glacier (Vallée Blanche via Skyway); alt 3466||Monte Bianco|Skyway Monte Bianco separate ticket – note
IT1|La Thuile||IT|Aosta, Valle d'Aosta|Espace San Bernardo|km≥60||Espace San Bernardo|
IT1|Pila||IT|Aosta, Valle d'Aosta|Pila|km≥60||Pila|Gondola from Aosta town; road to Pila open
IT1|Gressoney-La-Trinité||IT|Aosta, Valle d'Aosta|Monterosa Ski|km≥60||Monterosa|
IT1|Champoluc||IT|Aosta, Valle d'Aosta|Monterosa Ski|km≥60||Monterosa|Ayas valley; Antagnod noted
IT1|Livigno||IT|Sondrio, Lombardy|Livigno|km≥60||Livigno|Access via Foscagno pass (open) from Bormio; Forcola di Livigno closed in winter; Munt la Schera tunnel (toll) from CH
IT1|Bormio||IT|Sondrio, Lombardy|Bormio (Cima Bianca)|alt 3012||Bormio|Stelvio pass closed in winter
IT1|Santa Caterina Valfurva||IT|Sondrio, Lombardy|Santa Caterina Valfurva|alt 2880||Santa Caterina|Gavia closed in winter
IT1|Madesimo||IT|Sondrio, Lombardy|Valchiavenna (Madesimo–Campodolcino)|alt 2948||Valchiavenna|Splügen pass closed in winter
IT1|Passo dello Stelvio||IT|Sondrio, Lombardy|Passo dello Stelvio|glacier (summer/autumn only)||Stelvio|Summer-only glacier ski area; pass road closed in winter – no winter operation
IT1|Ponte di Legno–Passo Tonale||IT|Brescia, Lombardy / Trento, Trentino|Pontedilegno-Tonale (Adamello Ski)|km≥60; glacier (Presena); alt 3000||Ponte di Legno|Presena glacier early-season
IT2|Madonna di Campiglio||IT|Trento, Trentino-Alto Adige|Skiarea Campiglio Dolomiti di Brenta|km≥60||Madonna di Campiglio|
IT2|Pinzolo||IT|Trento, Trentino-Alto Adige|Skiarea Campiglio Dolomiti di Brenta|km≥60||Madonna di Campiglio|
IT2|Folgarida–Marilleva||IT|Trento, Trentino-Alto Adige|Skiarea Campiglio Dolomiti di Brenta|km≥60||Madonna di Campiglio|Val di Sole bases
IT2|Val di Fassa||IT|Trento, Trentino-Alto Adige|Dolomiti Superski|km≥60 (Fassa–Carezza local pass)|||Canazei/Campitello/Alba/Pozza/Vigo/Moena = one row per brief
IT2|Alpe Lusia–San Pellegrino||IT|Trento, Trentino-Alto Adige / Belluno, Veneto|Dolomiti Superski (Tre Valli)|km≥60 (Tre Valli ~100 km)||Passo San Pellegrino|Moena (Lusia) and Falcade/Passo San Pellegrino
IT2|Val di Fiemme–Obereggen||IT|Trento, Trentino-Alto Adige / Bolzano|Dolomiti Superski|km≥60 (Fiemme–Obereggen pass ~110 km)|||Cavalese/Alpe Cermis, Predazzo/Latemar, Pampeago, Obereggen
IT2|San Martino di Castrozza–Passo Rolle||IT|Trento, Trentino-Alto Adige|Dolomiti Superski|km≥60||San Martino di Castrozza|
IT2|Folgaria–Lavarone||IT|Trento, Trentino-Alto Adige|Alpe Cimbra|km≥60 (74 km)||Folgaria|
IT2|Pejo||IT|Trento, Trentino-Alto Adige|Pejo 3000 (Val di Sole)|alt 3000||Pejo|
IT2|Val Gardena|Gröden|IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|km≥60||Val Gardena|Ortisei/S. Cristina/Selva = one row
IT2|Alta Badia||IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|km≥60||Alta Badia|Corvara/Colfosco/La Villa/San Cassiano/Badia = one row
IT2|Kronplatz|Plan de Corones|IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|km≥60||Kronplatz|Brunico/Valdaora/San Vigilio bases
IT2|3 Zinnen Dolomites|Tre Cime Dolomiti|IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|km≥60||3 Zinnen|Sesto/San Candido/Dobbiaco
IT2|Alpe di Siusi|Seiser Alm|IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|km≥60 (73 km local)||Alpe di Siusi|Access road restrictions to Compatsch (permit/parking) – note
IT2|Plose||IT|Bolzano, Trentino-Alto Adige|Dolomiti Superski|listed in brief (Dolomiti Superski valley area); verify km||Plose|Bressanone/Brixen
IT2|Val Senales|Schnalstal|IT|Bolzano, Trentino-Alto Adige|Val Senales Glacier (Ortler Skiarena)|glacier; alt 3212||Val Senales|Autumn glacier opening
IT2|Solda|Sulden|IT|Bolzano, Trentino-Alto Adige|Sulden am Ortler (Ortler Skiarena)|alt 3250||Sulden|
IT2|Belpiano–Malga San Valentino|Schöneben–Haideralm|IT|Bolzano, Trentino-Alto Adige|Schöneben–Haideralm (Resia / Reschenpass)|km≥60 (65 km)||Belpiano|
IT2|Cortina d'Ampezzo||IT|Belluno, Veneto|Dolomiti Superski|km≥60; alt 2828||Cortina|Tofana/Faloria/Cinque Torri/Lagazuoi
IT2|Arabba–Marmolada||IT|Belluno, Veneto|Dolomiti Superski|km≥60; glacier (Marmolada); alt 3269||Arabba|
IT2|Civetta||IT|Belluno, Veneto|Dolomiti Superski|km≥60||Civetta|Alleghe/Selva di Cadore/Zoldo
AT1|St. Anton am Arlberg||AT|Tyrol|Ski Arlberg|km≥60; alt 2811; world-class freeride||Ski Arlberg|St. Christoph and Stuben noted as villages
AT1|Lech–Zürs||AT|Vorarlberg|Ski Arlberg|km≥60||Ski Arlberg|
AT1|Warth–Schröcken||AT|Vorarlberg|Ski Arlberg|km≥60||Ski Arlberg|Hochtannberg pass road normally open; Warth–Lech road closed in winter
AT1|Ischgl||AT|Tyrol|Silvretta Arena (Ischgl–Samnaun)|km≥60; alt 2872||Ischgl|Dynamic pricing? check
AT1|Kappl||AT|Tyrol|Kappl (Paznaun)|FWQ Open Faces 3* venue; Freeride Junior World Champs (criterion 3)|||
AT1|Galtür||AT|Tyrol|Galtür Silvapark (Paznaun)|ski-touring destination (Silvretta) (criterion 3)|||Silvretta Hochalpenstrasse closed in winter
AT1|Serfaus-Fiss-Ladis||AT|Tyrol|Serfaus-Fiss-Ladis|km≥60; alt 2828||Serfaus|Three villages, one row
AT1|Nauders||AT|Tyrol|Nauders am Reschenpass|km≥60||Nauders|Reschen pass open in winter
AT1|Sölden||AT|Tyrol|Sölden|km≥60; glacier (Rettenbach/Tiefenbach); alt 3340||Sölden|Autumn glacier opening; Timmelsjoch closed
AT1|Obergurgl–Hochgurgl||AT|Tyrol|Gurgl|km≥60; alt 3030; Open Faces FWQ||Gurgl|
AT1|Vent||AT|Tyrol|Vent (Ötztal)|ski-touring hub (Wildspitze) (criterion 3)|||Tiny lift area; include for touring
AT1|Kühtai||AT|Tyrol|Kühtai–Hochoetz|touring 4.0 anchor in brief; FWQ junior venue; km with Hochoetz pass|||Highest village in Austria (2020 m)
AT1|Axamer Lizum||AT|Tyrol|Axamer Lizum (Innsbruck)|Open Faces FWQ venue (criterion 3)|||
AT1|Stubai Glacier|Stubaier Gletscher|AT|Tyrol|Stubai Glacier (Neustift)|glacier; alt 3210||Stubai|
AT1|Kaunertal Glacier|Kaunertaler Gletscher|AT|Tyrol|Kaunertal Glacier (Feichten)|glacier; alt 3113||Kaunertal|
AT1|Pitztal Glacier|Pitztaler Gletscher|AT|Tyrol|Pitztal Glacier & Rifflsee (St. Leonhard/Mandarfen)|glacier; alt 3440||Pitztal|Rifflsee on same pass
AT1|Schruns – Silvretta Montafon Hochjoch||AT|Vorarlberg|Silvretta Montafon|km≥60||Silvretta Montafon|Hochjoch sector base
AT1|Gaschurn–St. Gallenkirch – Silvretta Montafon Nova||AT|Vorarlberg|Silvretta Montafon|km≥60; Open Faces FWQ history||Silvretta Montafon|Nova sector
AT1|Gargellen||AT|Vorarlberg|Gargellen (Montafon)|freeride/touring destination (Madrisa) (criterion 3)|||
AT1|Damüls–Mellau||AT|Vorarlberg|Damüls–Mellau (Bregenzerwald)|km≥60 (76 km)||Dam|
AT1|Kleinwalsertal||AT|Vorarlberg|Oberstdorf–Kleinwalsertal (two-country pass, ~130 km)|km≥60 on standard two-country day pass||Fellhorn|Riezlern/Hirschegg/Mittelberg; road access only via Oberstdorf (DE)
AT1|Garmisch-Partenkirchen||DE|Bavaria|Zugspitze & Garmisch-Classic|glacier (Zugspitzplatt – verify still lift-served glacier) (criterion 2)||Garmisch-Classic|Two areas; Zugspitze day ticket vs Garmisch-Classic ticket – note
AT1|Oberstdorf||DE|Bavaria|Oberstdorf–Kleinwalsertal (two-country pass, ~130 km)|km≥60 on standard day pass (Nebelhorn, Fellhorn/Kanzelwand, Söllereck)||Fellhorn|
AT2|Mayrhofen||AT|Tyrol|Mayrhofen (Penken/Ahorn) – Zillertal 3000|km≥60||Mayrhofen|Harakiri; Eggalm/Rastkogel
AT2|Hintertux Glacier|Hintertuxer Gletscher|AT|Tyrol|Hintertux Glacier – Zillertal 3000|glacier, year-round; alt 3250||Hintertux|365-day glacier
AT2|Hochzillertal–Hochfügen||AT|Tyrol|Hochzillertal–Hochfügen (Kaltenbach/Fügen)|km≥60 (89 km)||Kaltenbach|
AT2|Zell am Ziller||AT|Tyrol|Zillertal Arena|km≥60||Zillertal Arena|
AT2|Gerlos||AT|Tyrol|Zillertal Arena|km≥60||Zillertal Arena|Gerlos pass open in winter
AT2|Königsleiten–Wald||AT|Salzburg|Zillertal Arena|km≥60||Zillertal Arena|Incl. Hochkrimml
AT2|Kitzbühel||AT|Tyrol|KitzSki|km≥60||KitzSki|Incl. Jochberg, Pass Thurn
AT2|Kirchberg in Tirol||AT|Tyrol|KitzSki|km≥60||KitzSki|
AT2|Söll||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|
AT2|Ellmau||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|Going noted as village
AT2|Scheffau||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|
AT2|Westendorf||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|
AT2|Brixen im Thale||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|
AT2|Hopfgarten im Brixental||AT|Tyrol|SkiWelt Wilder Kaiser-Brixental|km≥60||SkiWelt|Itter noted as village
AT2|Alpbach||AT|Tyrol|Ski Juwel Alpbachtal Wildschönau|km≥60; Open Faces FWQ history||Ski Juwel|
AT2|Wildschönau||AT|Tyrol|Ski Juwel Alpbachtal Wildschönau|km≥60||Ski Juwel|Niederau/Oberau/Auffach
AT2|Fieberbrunn||AT|Tyrol|Skicircus Saalbach Hinterglemm Leogang Fieberbrunn|km≥60; FWT stop (Wildseeloder)||Saalbach|
AT3|Saalbach-Hinterglemm||AT|Salzburg|Skicircus Saalbach Hinterglemm Leogang Fieberbrunn|km≥60||Saalbach|
AT3|Leogang||AT|Salzburg|Skicircus Saalbach Hinterglemm Leogang Fieberbrunn|km≥60||Saalbach|
AT3|Zell am See||AT|Salzburg|Schmittenhöhe (Zell am See-Kaprun)|km≥60 (77 km)||Schmittenh|
AT3|Kaprun – Kitzsteinhorn||AT|Salzburg|Kitzsteinhorn–Maiskogel (Zell am See-Kaprun)|glacier; alt 3029; FWQ history||Kitzsteinhorn|
AT3|Wildkogel (Neukirchen–Bramberg)||AT|Salzburg|Wildkogel-Arena|km≥60 (75 km)||Wildkogel|
AT3|Flachau||AT|Salzburg|Snow Space Salzburg|km≥60||Snow Space|
AT3|Wagrain||AT|Salzburg|Snow Space Salzburg|km≥60||Snow Space|
AT3|St. Johann–Alpendorf||AT|Salzburg|Snow Space Salzburg|km≥60||Snow Space|
AT3|Hochkönig (Maria Alm–Dienten–Mühlbach)||AT|Salzburg|Hochkönig|km≥60||Hochk|One row for three villages
AT3|Bad Gastein||AT|Salzburg|Ski amadé – Gastein (Stubnerkogel/Graukogel/Sportgastein)|km≥60; Sportgastein freeride/FWQ history||Bad Gastein|Sportgastein incl.
AT3|Bad Hofgastein||AT|Salzburg|Ski amadé – Gastein (Schlossalm–Angertal)|km≥60||Bad Gastein|
AT3|Großarl–Dorfgastein||AT|Salzburg|Ski amadé – Großarltal-Dorfgastein|km≥60 (67.5 km)||Dorfgastein|
AT3|Obertauern||AT|Salzburg|Obertauern|km≥60||Obertauern|
AT3|Schladming||AT|Styria|Schladming-Dachstein 4-Berge-Skischaukel|km≥60||Schladming|Planai/Hochwurzen/Hauser Kaibling/Reiteralm
AT3|Dachstein Glacier (Ramsau)|Dachstein Gletscher|AT|Styria|Schladming-Dachstein|glacier (criterion 2) – VERIFY alpine ski lifts still operate; may have ended 2023|||If glacier ski operation has ended, mark EXCLUDE
AT3|Katschberg||AT|Carinthia / Salzburg|Katschberg–Aineck|km≥60 (80 km)||Katschberg|
AT3|Bad Kleinkirchheim||AT|Carinthia|Bad Kleinkirchheim–St. Oswald|km≥60||Bad Kleinkirchheim|
AT3|Nassfeld||AT|Carinthia|Nassfeld–Hermagor|km≥60||Nassfeld|Passo Pramollo from Pontebba closed in winter – access via Tarvisio/Hermagor
AT3|Mölltal Glacier|Mölltaler Gletscher|AT|Carinthia|Mölltal Glacier (Flattach)|glacier; alt 3122||Moelltal|
AT3|Heiligenblut – Großglockner||AT|Carinthia|Grossglockner Heiligenblut|alt 2902; freeride||Heiligenblut|Grossglockner Hochalpenstrasse closed in winter
CH1|Champéry||CH|Valais|Portes du Soleil|km≥60||Portes du Soleil|Incl. Les Crosets/Champoussin (Val-d'Illiez)
CH1|Morgins||CH|Valais|Portes du Soleil|km≥60||Portes du Soleil|
CH1|Verbier||CH|Valais|4 Vallées|km≥60; glacier (Mont Fort); alt 3330; FWT Xtreme||4 Vall|Bruson and La Tzoumaz noted
CH1|Nendaz||CH|Valais|4 Vallées|km≥60; FWQ venue||4 Vall|
CH1|Veysonnaz||CH|Valais|4 Vallées|km≥60||4 Vall|
CH1|Thyon||CH|Valais|4 Vallées|km≥60||4 Vall|Thyon 2000/Les Collons
CH1|Zermatt||CH|Valais|Matterhorn Ski Paradise (Zermatt–Cervinia)|km≥60; glacier year-round; alt 3899|Täsch|Zermatt/Breuil|Car-free: road head Täsch
CH1|Saas-Fee||CH|Valais|Saas-Fee (Saastal)|km≥60; glacier; alt 3573||Saas-Fee|Car-free village; parking at village entrance (car journey ends at Saas-Fee)
CH1|Saas-Grund – Hohsaas||CH|Valais|Saastal (Hohsaas)|alt 3200||Hohsaas|
CH1|Crans-Montana||CH|Valais|Crans-Montana|km≥60; glacier (Plaine Morte); alt 2927; FWQ 2026||Crans-Montana|Dynamic pricing? check
CH1|Grimentz–Zinal||CH|Valais|Val d'Anniviers|km≥60; alt 2900; FWQ history||Grimentz|
CH1|Saint-Luc–Chandolin||CH|Valais|Val d'Anniviers|km≥60 (60 km); alt 2980||Saint Luc|
CH1|Aletsch Arena||CH|Valais|Aletsch Arena (Riederalp/Bettmeralp/Fiesch-Eggishorn)|km≥60; alt 2869|Mörel/Betten/Fiesch (valley stations)|Aletsch Arena|Car-free plateau; road head = valley cable-car stations (use Fiesch or Betten Talstation – state which)
CH1|Grächen||CH|Valais|Grächen|alt 2864||Gr|Family resort; criterion 4 only
CH1|Lauchernalp – Lötschental||CH|Valais|Lauchernalp|alt 3100; freeride/touring||Lauchernalp|Wiler valley station
CH1|Belalp – Blatten||CH|Valais|Belalp|alt 3118; freeride||Belalp|Blatten bei Naters valley station
CH1|Arolla||CH|Valais|Arolla (Val d'Hérens)|alt 2877; Haute Route stage; touring hub||Arolla|
CH1|Villars–Gryon||CH|Vaud|Villars–Gryon–Les Diablerets (Alpes Vaudoises)|km≥60 (87 km)||Villars|
CH1|Les Diablerets – Glacier 3000||CH|Vaud|Villars–Gryon–Les Diablerets / Glacier 3000 (Alpes Vaudoises, Gstaad)|glacier (Glacier 3000); alt 3016||Glacier 3000|Glacier 3000 base Col du Pillon; Les Diablerets village
CH1|Leysin||CH|Vaud|Leysin (Alpes Vaudoises)|km≥60 (60 km); FWQ 2026 venue||Leysin|
CH2|Grindelwald||CH|Bern|Jungfrau Ski Region|km≥60 (Grindelwald-Wengen 101 km + First)||Kleine Scheidegg|Eiger Express
CH2|Wengen||CH|Bern|Jungfrau Ski Region|km≥60|Lauterbrunnen|Kleine Scheidegg|Car-free: road head Lauterbrunnen
CH2|Mürren – Schilthorn||CH|Bern|Jungfrau Ski Region|alt 2970; freeride (Inferno)|Lauterbrunnen (Stechelberg)|Schilthorn|Car-free: road head Lauterbrunnen or Stechelberg – state which
CH2|Gstaad||CH|Bern|Gstaad Mountain Rides (Saanenland)|km≥60||Rinderberg|Incl. Saanenmöser/Schönried/Zweisimmen/St. Stephan (Rinderberg) – one row
CH2|Adelboden||CH|Bern|Adelboden–Lenk|km≥60||Adelboden|
CH2|Lenk||CH|Bern|Adelboden–Lenk|km≥60||Adelboden|
CH2|Meiringen-Hasliberg||CH|Bern|Meiringen-Hasliberg|km≥60 (60 km)||Meiringen|
CH2|Engelberg||CH|Obwalden|Engelberg–Titlis|km≥60; glacier (Titlis); alt 3020; world-class freeride||Titlis|
CH2|Andermatt||CH|Uri|SkiArena Andermatt-Sedrun-Disentis|km≥60; alt 2961 (Gemsstock); world-class freeride||Andermatt/Oberalp|Oberalp road closed in winter (car train Andermatt–Sedrun not counted); Gotthard tunnel open
CH2|Sedrun||CH|Graubünden|SkiArena Andermatt-Sedrun-Disentis|km≥60||Andermatt/Oberalp|Access from Milan: Oberalp and Lukmanier CLOSED – route via Chur/Reichenau–Disentis
CH2|Disentis||CH|Graubünden|SkiArena Andermatt-Sedrun-Disentis|km≥60 (60 km); alt 2833; FWQ history||Disentis|Lukmanier pass closed in winter (treat as closed) – route via Chur
CH2|Flumserberg||CH|St. Gallen|Flumserberg|km≥60 (65 km)||Flumserberg|
CH2|Arosa||CH|Graubünden|Arosa Lenzerheide|km≥60; alt 2865||Arosa Lenzerheide|
CH2|Lenzerheide||CH|Graubünden|Arosa Lenzerheide|km≥60||Arosa Lenzerheide|Incl. Valbella/Churwalden/Parpan
CH2|Laax||CH|Graubünden|LAAX (Flims–Laax–Falera)|km≥60; glacier (Vorab); alt 3018||Laax|Flims/Falera villages – one row
CH2|St. Moritz||CH|Graubünden|Engadin St. Moritz (Corviglia)|km≥60; alt 3057||St. Moritz|Celerina; Julier or Maloja open, Albula road closed
CH2|Corvatsch – Silvaplana/Sils||CH|Graubünden|Engadin St. Moritz (Corvatsch–Furtschellas)|km≥60; glacier (Corvatsch); alt 3303||Corvatsch|
CH2|Diavolezza–Lagalb (Pontresina)||CH|Graubünden|Engadin St. Moritz (Val Bernina)|glacier; alt 3006||Diavolezza|Bernina pass open in winter (from Italian side via Tirano)
CH2|Obersaxen–Mundaun||CH|Graubünden|Obersaxen Mundaun Val Lumnezia (Surselva)|km≥60 (120 km)||Obersaxen|
CH2|Savognin||CH|Graubünden|Savognin|km≥60 (73.5 km)||Savognin|Julier route
CH2|Scuol||CH|Graubünden|Scuol – Motta Naluns (Engadin Samnaun Val Müstair)|km≥60 (70 km)||Scuol|Access via Ofen pass or Landeck/Reschen; Flüela closed
CH2|Samnaun||CH|Graubünden|Silvretta Arena (Ischgl–Samnaun)|km≥60||Ischgl|Duty-free; access via Austria (Spiss road)
CH2|Davos||CH|Graubünden|Davos Klosters (Parsenn/Jakobshorn/Pischa/Rinerhorn)|km≥60; alt 2844||Parsenn|Flüela closed: via Landquart–Klosters or Vereina car train
CH2|Klosters||CH|Graubünden|Davos Klosters (Parsenn/Madrisa)|km≥60||Parsenn|
CH2|Vals||CH|Graubünden|Vals – Dachberg|alt 2851 (criterion 4 only)||Vals|Small area; include per criterion 4 with note
"""

rows = []
for line in C.strip().splitlines():
    p = [x.strip() for x in line.split('|')]
    assert len(p) == 10, (len(p), line)
    batch, name, local, cc, region, area, basis, rh, match, notes = p
    url = find(match) if match else ''
    if match and not url:
        print("NO MATCH:", name, match)
    rows.append(dict(id=len(rows) + 1, batch=batch, resort_name=name, local_name=local, country=cc, region=region,
                     ski_area=area, inclusion_basis=basis, road_head_hint=rh, skiresort_url=url, notes_for_agent=notes))

with open("../candidates.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("TOTAL", len(rows))
print(Counter(r['country'] for r in rows))
print(Counter(r['batch'] for r in rows))
os.makedirs("lists", exist_ok=True)
for b in sorted(set(r['batch'] for r in rows)):
    sub = [r for r in rows if r['batch'] == b]
    with open(f"lists/list_{b}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sub[0].keys())); w.writeheader(); w.writerows(sub)
names = Counter((r['resort_name'], r['country']) for r in rows)
print("duplicates:", [k for k, v in names.items() if v > 1])
