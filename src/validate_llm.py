"""
T3 — LLM Extraction Validation (93 samples)
"""
import pandas as pd
import os

OUTPUT_DIR = "gdelt_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

llm_outputs = [
    {"id":1,"headline":"Taiwan semiconductor orders decline for third consecutive month amid geopolitical tensions","disruption_category":"geopolitical","affected_industry":"semiconductor","region":"Taiwan","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":2,"headline":"Ever Given container ship runs aground blocking Suez Canal entirely","disruption_category":"port","affected_industry":"automotive","region":"Egypt","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":3,"headline":"Toyota halts US assembly lines as Japanese chip shortages reach North American plants","disruption_category":"factory","affected_industry":"semiconductor","region":"North America","severity_score":4,"propagation_risk":"regional","signal_type":"Amplifier"},
    {"id":4,"headline":"Biden invokes Defense Production Act to accelerate domestic semiconductor manufacturing","disruption_category":"trade_policy","affected_industry":"semiconductor","region":"United States","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":5,"headline":"Suez Canal fully reopened as Ever Given refloated after six day blockage","disruption_category":"port","affected_industry":"automotive","region":"Egypt","severity_score":5,"propagation_risk":"global","signal_type":"Recovery"},
    {"id":6,"headline":"Dockworkers strike at LA port compounds already critical chip shortage for automakers","disruption_category":"labor","affected_industry":"semiconductor","region":"United States","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":7,"headline":"Monsoon floods damage key rail links used to reroute cargo after Red Sea crisis","disruption_category":"weather","affected_industry":"automotive","region":"unknown","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":8,"headline":"TSMC Fab 14 forced to halt production after major fire destroys cleanroom","disruption_category":"factory","affected_industry":"semiconductor","region":"unknown","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":9,"headline":"Semiconductor lead times fall below 20 weeks for first time since 2020 chip crisis","disruption_category":"factory","affected_industry":"semiconductor","region":"unknown","severity_score":1,"propagation_risk":"none","signal_type":"Recovery"},
    {"id":10,"headline":"Red Sea shipping delays now hitting food retailers in West Africa UN warns","disruption_category":"port","affected_industry":"food","region":"West Africa","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":11,"headline":"China imposes export restrictions on rare earth minerals used in EV batteries","disruption_category":"trade_policy","affected_industry":"automotive","region":"China","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":12,"headline":"Russian oil sanctions force European refineries to seek alternative suppliers","disruption_category":"geopolitical","affected_industry":"energy","region":"Europe","severity_score":4,"propagation_risk":"regional","signal_type":"Trigger"},
    {"id":13,"headline":"Apple shifts iPhone production from China to India amid geopolitical tensions","disruption_category":"geopolitical","affected_industry":"general","region":"China, India","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":14,"headline":"Global container shipping rates hit record high as demand surges post pandemic","disruption_category":"port","affected_industry":"logistics","region":"global","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":15,"headline":"ASML restricts shipment of chip making equipment to China following US pressure","disruption_category":"trade_policy","affected_industry":"semiconductor","region":"China","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":16,"headline":"Volkswagen announces closure of three German factories amid EV transition challenges","disruption_category":"factory","affected_industry":"automotive","region":"Germany","severity_score":4,"propagation_risk":"regional","signal_type":"Amplifier"},
    {"id":17,"headline":"Samsung Austin fab resumes production after Texas winter storm power outages","disruption_category":"weather","affected_industry":"energy","region":"United States","severity_score":4,"propagation_risk":"local","signal_type":"Recovery"},
    {"id":18,"headline":"India imposes export ban on wheat following domestic shortage concerns","disruption_category":"trade_policy","affected_industry":"food","region":"India","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":19,"headline":"Maersk reroutes vessels around Cape of Good Hope avoiding Red Sea entirely","disruption_category":"geopolitical","affected_industry":"general","region":"Red Sea","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":20,"headline":"Ukraine grain export corridor suspended following Russian withdrawal from deal","disruption_category":"geopolitical","affected_industry":"food","region":"Ukraine","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":21,"headline":"BASF cuts chemical output by 25 percent due to European energy rationing","disruption_category":"geopolitical","affected_industry":"energy","region":"Europe","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":22,"headline":"Philippine typhoon disrupts electronics manufacturing in Clark economic zone","disruption_category":"weather","affected_industry":"semiconductor","region":"Philippines","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":23,"headline":"US imposes 100 percent tariffs on Chinese electric vehicles effective immediately","disruption_category":"trade_policy","affected_industry":"general","region":"North America","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":24,"headline":"Lithium carbonate prices crash 80 percent disrupting battery supply chain planning","disruption_category":"Market Fluctuation","affected_industry":"automotive","region":"Global","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":25,"headline":"Boeing 737 MAX grounded globally following second fatal crash in five months","disruption_category":"Product Safety & Quality","affected_industry":"general","region":"Global","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":26,"headline":"Shanghai port throughput falls 40 percent during two month COVID lockdown","disruption_category":"Logistics disruption","affected_industry":"logistics","region":"East Asia","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":27,"headline":"Panama Canal reduces daily transits by half due to historic drought water levels","disruption_category":"weather","affected_industry":"automotive","region":"Central America","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":28,"headline":"Houthi militants attack Maersk container vessel in Red Sea with missile strike","disruption_category":"geopolitical","affected_industry":"logistics","region":"Red Sea","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":29,"headline":"UAW strikes Ford GM and Stellantis simultaneously for first time in history","disruption_category":"labor","affected_industry":"automotive","region":"North America","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":30,"headline":"Key Bridge Baltimore collapse closes major US auto import port for months","disruption_category":"Infrastructure Failure","affected_industry":"automotive","region":"United States","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":31,"headline":"TSMC evacuates fabs temporarily following 7.4 magnitude Taiwan earthquake","disruption_category":"weather","affected_industry":"semiconductor","region":"Taiwan","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":32,"headline":"EU launches anti dumping investigation into Chinese solar panel imports","disruption_category":"geopolitical","affected_industry":"energy","region":"Europe","severity_score":3,"propagation_risk":"regional","signal_type":"Propagation"},
    {"id":33,"headline":"Foxconn Zhengzhou iPhone factory output cut as worker protests intensify","disruption_category":"labor","affected_industry":"general","region":"China","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":34,"headline":"Japan restricts export of chipmaking chemicals to China following US lead","disruption_category":"geopolitical","affected_industry":"semiconductor","region":"Japan, China","severity_score":4,"propagation_risk":"regional","signal_type":"Propagation"},
    {"id":35,"headline":"Brazilian drought threatens soybean harvest and global food supply chains","disruption_category":"weather","affected_industry":"food","region":"Brazil","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":36,"headline":"German pharmaceutical company halts API production due to gas supply cuts","disruption_category":"Utility disruption","affected_industry":"energy","region":"Germany","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":37,"headline":"Mexico overtakes China as top US trading partner amid nearshoring trend","disruption_category":"Supply Chain Restructuring","affected_industry":"general","region":"North America, Asia-Pacific","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":38,"headline":"Nordic semiconductor fab announces 6 month delay due to equipment shortages","disruption_category":"Equipment Shortage","affected_industry":"semiconductor","region":"Nordic","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":39,"headline":"Australia halts lithium spodumene exports amid price collapse and oversupply","disruption_category":"Economic/Market Fluctuation","affected_industry":"automotive","region":"Australia","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":40,"headline":"Italian automotive supplier files bankruptcy amid EV transition difficulties","disruption_category":"geopolitical","affected_industry":"automotive","region":"Italy","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":41,"headline":"South Korean battery maker LG Energy announces US gigafactory delay","disruption_category":"Production Delay","affected_industry":"energy","region":"North America (US)","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":42,"headline":"Taiwanese PCB manufacturers report order cancellations from US customers","disruption_category":"trade_policy","affected_industry":"logistics","region":"Taiwan, United States","severity_score":4,"propagation_risk":"regional","signal_type":"Amplifier"},
    {"id":43,"headline":"French port workers strike halts fuel distribution across northern France","disruption_category":"labor","affected_industry":"logistics","region":"Northern France","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":44,"headline":"Bangladesh garment factory closures spike amid labor unrest and flooding","disruption_category":"weather","affected_industry":"general","region":"Bangladesh","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":45,"headline":"Chilean copper mine strike enters third week threatening global supply","disruption_category":"labor","affected_industry":"general","region":"South America","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":46,"headline":"Vietnam electronics exports fall sharply as Samsung shifts orders to India","disruption_category":"Supply Chain Restructuring","affected_industry":"semiconductor","region":"Vietnam","severity_score":4,"propagation_risk":"local","signal_type":"Trigger"},
    {"id":47,"headline":"Canadian rail strike disrupts grain potash and auto parts shipments coast to coast","disruption_category":"labor","affected_industry":"automotive","region":"Canada","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":48,"headline":"Indonesia bans nickel ore exports to force domestic battery processing investment","disruption_category":"trade_policy","affected_industry":"automotive","region":"Indonesia","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":49,"headline":"Myanmar coup disrupts garment supply chains for European fashion brands","disruption_category":"Political Instability","affected_industry":"general","region":"Southeast Asia","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":50,"headline":"Turkish lira collapse forces auto parts suppliers to halt dollar denominated contracts","disruption_category":"geopolitical","affected_industry":"automotive","region":"Turkey","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":51,"headline":"Pfizer API supplier in India shuts down following FDA inspection failure","disruption_category":"Regulatory Compliance","affected_industry":"pharmaceutical","region":"India","severity_score":4,"propagation_risk":"local","signal_type":"Trigger"},
    {"id":52,"headline":"Amazon warns of holiday season delays due to port congestion and driver shortage","disruption_category":"Logistics disruption","affected_industry":"logistics","region":"Global","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":53,"headline":"Qualcomm reports 6 month chip lead times as smartphone demand recovery stalls","disruption_category":"Component Shortage","affected_industry":"semiconductor","region":"Global","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":54,"headline":"OPEC plus cuts oil production by 2 million barrels per day amid recession fears","disruption_category":"Supply Shortage","affected_industry":"energy","region":"Global","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":55,"headline":"Greek shipping strike halts Mediterranean cargo operations for second week","disruption_category":"labor","affected_industry":"automotive","region":"Mediterranean, Greece","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":56,"headline":"Pakistani floods destroy cotton crop threatening global textile supply chains","disruption_category":"weather","affected_industry":"general","region":"Pakistan","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":57,"headline":"Sri Lanka economic collapse disrupts tea and rubber export supply chains","disruption_category":"geopolitical","affected_industry":"food","region":"Sri Lanka","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":58,"headline":"Morocco phosphate export disruption threatens global fertilizer availability","disruption_category":"Supply Shortage","affected_industry":"logistics","region":"Morocco","severity_score":5,"propagation_risk":"global","signal_type":"Recovery"},
    {"id":59,"headline":"Nigerian oil pipeline sabotage cuts production by 200000 barrels per day","disruption_category":"geopolitical","affected_industry":"energy","region":"Nigeria (West Africa)","severity_score":4,"propagation_risk":"regional","signal_type":"Trigger"},
    {"id":60,"headline":"Taiwan Strait military exercises disrupt commercial shipping lane traffic","disruption_category":"geopolitical","affected_industry":"logistics","region":"Taiwan Strait","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":61,"headline":"South African port congestion reaches crisis levels amid infrastructure failures","disruption_category":"Logistics & Infrastructure","affected_industry":"automotive","region":"South Africa","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":62,"headline":"Japanese auto production cut due to legacy chip shortage from Malaysian fab fire","disruption_category":"Supply Shortage","affected_industry":"semiconductor","region":"Japan","severity_score":4,"propagation_risk":"regional","signal_type":"Trigger"},
    {"id":63,"headline":"US China chip war escalates as Beijing restricts gallium and germanium exports","disruption_category":"geopolitical","affected_industry":"semiconductor","region":"Global","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":64,"headline":"European steel mills shut down as energy costs make production unviable","disruption_category":"Economic","affected_industry":"energy","region":"Europe","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":65,"headline":"Indian pharmaceutical regulator bans 14 drug formulations citing quality issues","disruption_category":"Quality Failure","affected_industry":"pharmaceutical","region":"India","severity_score":4,"propagation_risk":"regional","signal_type":"Amplifier"},
    {"id":66,"headline":"Mexico avocado export disruption as cartel roadblocks cut Michoacan supply routes","disruption_category":"geopolitical","affected_industry":"automotive","region":"Latin America","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":67,"headline":"Kenyan flower exports collapse as cold chain logistics break down at Nairobi airport","disruption_category":"Logistics Failure","affected_industry":"food","region":"East Africa","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":68,"headline":"Singapore semiconductor equipment firm reports 18 month delivery backlog","disruption_category":"Supply Disruption","affected_industry":"semiconductor","region":"Singapore","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":69,"headline":"Dutch horticultural exports disrupted by trucker protest blocking highways","disruption_category":"port","affected_industry":"logistics","region":"Netherlands","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":70,"headline":"Peru copper mine forced to suspend operations after community blockade","disruption_category":"geopolitical","affected_industry":"general","region":"South America","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":71,"headline":"Thailand auto parts exports fall as Japanese OEM orders cut amid chip shortage","disruption_category":"Supply Shortage","affected_industry":"semiconductor","region":"Thailand, Japan","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":72,"headline":"Romanian wheat harvest failure worsens European food supply concerns","disruption_category":"Supply Shortage","affected_industry":"food","region":"Romania, Europe","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":73,"headline":"Taiwanese notebook makers shift final assembly to Vietnam amid China risk","disruption_category":"geopolitical","affected_industry":"general","region":"Taiwan, Vietnam, China","severity_score":3,"propagation_risk":"regional","signal_type":"Amplifier"},
    {"id":74,"headline":"US West Coast dockworker contract talks collapse raising strike threat","disruption_category":"labor","affected_industry":"general","region":"US West Coast","severity_score":5,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":75,"headline":"Chinese battery manufacturer CATL pauses European gigafactory investment","disruption_category":"Investment delay / Capacity reduction","affected_industry":"automotive","region":"Europe","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":76,"headline":"Finnish pulp mill strike disrupts European packaging material supply","disruption_category":"labor","affected_industry":"general","region":"Europe","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":77,"headline":"Turkish steel exports surge as Russian supply cut from Western markets","disruption_category":"geopolitical","affected_industry":"logistics","region":"Global","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":78,"headline":"Colombian port strike disrupts coffee banana and coal export schedules","disruption_category":"labor","affected_industry":"logistics","region":"Colombia","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":79,"headline":"Philippine semiconductor assembly plant damaged by flooding in Laguna province","disruption_category":"weather","affected_industry":"semiconductor","region":"Philippines","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":80,"headline":"Swiss watchmaker Swatch reports movement component shortage from Asian suppliers","disruption_category":"Component Shortage","affected_industry":"logistics","region":"Asia","severity_score":4,"propagation_risk":"regional","signal_type":"Propagation"},
    {"id":81,"headline":"Bangladeshi ready made garment exports drop as brands diversify to Vietnam","disruption_category":"Market Shift","affected_industry":"logistics","region":"Bangladesh","severity_score":3,"propagation_risk":"regional","signal_type":"Trigger"},
    {"id":82,"headline":"Egyptian Suez Canal revenues surge as Red Sea crisis diverts traffic northward","disruption_category":"geopolitical","affected_industry":"automotive","region":"Red Sea Region","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":83,"headline":"Indonesian palm oil export ban causes global food inflation concerns","disruption_category":"trade_policy","affected_industry":"energy","region":"Global","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":84,"headline":"Kenyan tea auction suspended following drought and infrastructure collapse","disruption_category":"weather","affected_industry":"food","region":"Kenya","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":85,"headline":"Cambodian garment factories close as European fast fashion brands cut orders","disruption_category":"Demand Shock","affected_industry":"general","region":"Cambodia","severity_score":5,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":86,"headline":"Mexican auto exports hit record high as nearshoring accelerates post pandemic","disruption_category":"Market Shift","affected_industry":"automotive","region":"North America","severity_score":1,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":87,"headline":"Norwegian salmon farming disrupted by sea lice outbreak affecting exports","disruption_category":"Biological Contamination","affected_industry":"food","region":"Norway","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
    {"id":88,"headline":"Ghanaian cocoa output falls sharply amid disease and climate stress","disruption_category":"weather","affected_industry":"food","region":"West Africa","severity_score":5,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":89,"headline":"US semiconductor CHIPS Act funding delays frustrate fab construction timelines","disruption_category":"geopolitical","affected_industry":"semiconductor","region":"United States","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":90,"headline":"European wind turbine supply chain faces steel and rare earth bottlenecks","disruption_category":"Supply Shortage","affected_industry":"energy","region":"Europe","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":91,"headline":"South Korean shipyard order backlog hits 3 year high amid vessel shortage","disruption_category":"Supply Shortage","affected_industry":"general","region":"South Korea","severity_score":4,"propagation_risk":"global","signal_type":"Amplifier"},
    {"id":92,"headline":"Indian steel exports surge as China domestic demand weakens sharply","disruption_category":"Market Shift","affected_industry":"logistics","region":"Asia","severity_score":4,"propagation_risk":"global","signal_type":"Propagation"},
    {"id":93,"headline":"Brazilian iron ore shipments disrupted by Vale dam safety inspection closure","disruption_category":"Regulatory/Operational","affected_industry":"general","region":"Brazil","severity_score":4,"propagation_risk":"global","signal_type":"Trigger"},
]

manual_labels = [
    (1,  True,  True,  True,  True,  True,  False, "Signal should be Precursor not Amplifier"),
    (2,  True,  False, True,  True,  True,  True,  "Industry wrong: Suez = logistics not automotive"),
    (3,  False, False, True,  True,  False, False, "Category wrong: should be factory/labor; industry wrong: automotive not semiconductor; propagation global; signal Trigger"),
    (4,  True,  True,  True,  True,  True,  False, "Signal wrong: govt response = Response not Amplifier"),
    (5,  True,  False, True,  False, True,  True,  "Industry wrong: logistics not automotive; severity wrong: reopening = 2 not 5"),
    (6,  True,  False, True,  False, True,  True,  "Industry wrong: logistics not semiconductor; severity 4 not 5"),
    (7,  True,  False, False, True,  True,  True,  "Industry wrong: logistics not automotive; region wrong: unknown inferable as South/SE Asia"),
    (8,  True,  True,  False, True,  True,  True,  "Region wrong: unknown — TSMC is in Taiwan"),
    (9,  False, True,  False, True,  True,  True,  "Category wrong: Recovery event not factory; region wrong: Global not unknown"),
    (10, False, True,  True,  True,  True,  False, "Category wrong: geopolitical not port; signal Propagation not Amplifier"),
    (11, True,  True,  True,  True,  True,  True,  "All correct"),
    (12, True,  True,  True,  True,  False, True,  "Propagation wrong: Russian oil sanctions = global not regional"),
    (13, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not general"),
    (14, True,  True,  True,  True,  True,  True,  "All correct"),
    (15, True,  True,  True,  True,  True,  True,  "All correct"),
    (16, True,  True,  True,  True,  True,  True,  "All correct"),
    (17, False, False, True,  True,  True,  True,  "Category wrong: natural_disaster not weather; industry wrong: semiconductor not energy"),
    (18, True,  True,  True,  True,  True,  True,  "All correct"),
    (19, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not general"),
    (20, True,  True,  True,  True,  True,  True,  "All correct"),
    (21, False, False, True,  True,  True,  True,  "Category wrong: economic not geopolitical; industry wrong: chemical not energy"),
    (22, True,  True,  True,  True,  True,  True,  "All correct"),
    (23, True,  False, True,  True,  True,  True,  "Industry wrong: automotive not general"),
    (24, False, True,  True,  True,  True,  True,  "Category wrong: non-standard label 'Market Fluctuation'"),
    (25, False, False, True,  True,  True,  True,  "Category non-standard; industry wrong: aerospace not general"),
    (26, False, True,  False, True,  True,  True,  "Category non-standard 'Logistics disruption'; region wrong: China not East Asia"),
    (27, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not automotive"),
    (28, True,  True,  True,  True,  True,  True,  "All correct"),
    (29, True,  True,  True,  True,  True,  True,  "All correct"),
    (30, False, True,  True,  True,  True,  True,  "Category non-standard 'Infrastructure Failure'"),
    (31, False, True,  True,  True,  True,  True,  "Category wrong: natural_disaster not weather for earthquake"),
    (32, True,  True,  True,  True,  True,  True,  "All correct"),
    (33, False, False, True,  True,  True,  True,  "Category wrong: labor not geopolitical; industry wrong: electronics not general"),
    (34, True,  True,  True,  True,  False, True,  "Propagation wrong: chip chemicals = global not regional"),
    (35, True,  True,  True,  True,  True,  True,  "All correct"),
    (36, False, False, True,  True,  True,  True,  "Category non-standard 'Utility disruption'; industry wrong: pharmaceutical not energy"),
    (37, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Chain Restructuring'"),
    (38, False, True,  False, True,  True,  True,  "Category non-standard 'Equipment Shortage'; region vague: Nordic needs country"),
    (39, False, True,  True,  True,  True,  True,  "Category non-standard 'Economic/Market Fluctuation'"),
    (40, False, True,  True,  True,  True,  True,  "Category wrong: economic not geopolitical"),
    (41, False, False, False, True,  True,  True,  "Category non-standard 'Production Delay'; industry wrong: automotive not energy; region format inconsistent"),
    (42, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not logistics"),
    (43, True,  True,  True,  True,  True,  True,  "All correct"),
    (44, False, False, True,  True,  True,  True,  "Category wrong: labor primary cause; industry wrong: apparel not general"),
    (45, True,  False, True,  True,  True,  True,  "Industry wrong: mining not general"),
    (46, False, False, True,  True,  False, True,  "Category non-standard; industry wrong: electronics not semiconductor; propagation global not local"),
    (47, True,  True,  True,  True,  True,  True,  "All correct"),
    (48, True,  True,  True,  True,  True,  True,  "All correct"),
    (49, False, False, True,  True,  True,  True,  "Category non-standard 'Political Instability'; industry wrong: apparel not general"),
    (50, True,  True,  True,  True,  True,  True,  "All correct"),
    (51, False, True,  True,  True,  False, True,  "Category non-standard 'Regulatory Compliance'; propagation wrong: pharmaceutical API = global not local"),
    (52, False, True,  True,  True,  True,  True,  "Category non-standard 'Logistics disruption'"),
    (53, False, True,  True,  True,  True,  True,  "Category non-standard 'Component Shortage'"),
    (54, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Shortage'"),
    (55, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not automotive"),
    (56, True,  False, True,  True,  True,  True,  "Industry wrong: apparel not general"),
    (57, True,  True,  True,  True,  True,  True,  "All correct"),
    (58, False, False, True,  True,  True,  False, "Category non-standard; industry wrong: agriculture not logistics; signal wrong: Trigger not Recovery"),
    (59, True,  True,  True,  True,  True,  True,  "All correct"),
    (60, True,  True,  True,  True,  True,  True,  "All correct"),
    (61, False, False, True,  True,  True,  True,  "Category non-standard 'Logistics & Infrastructure'; industry wrong: logistics not automotive"),
    (62, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Shortage' — should be factory"),
    (63, True,  True,  True,  True,  True,  True,  "All correct"),
    (64, False, False, True,  True,  True,  True,  "Category too vague 'Economic'; industry wrong: manufacturing not energy"),
    (65, False, True,  True,  True,  False, True,  "Category non-standard 'Quality Failure'; propagation wrong: drug ban = global not regional"),
    (66, True,  False, True,  True,  True,  True,  "Industry wrong: food not automotive"),
    (67, False, True,  True,  True,  True,  True,  "Category non-standard 'Logistics Failure'"),
    (68, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Disruption'"),
    (69, False, True,  True,  True,  True,  True,  "Category wrong: labor not port"),
    (70, True,  False, True,  True,  True,  True,  "Industry wrong: mining not general"),
    (71, False, False, True,  True,  True,  True,  "Category non-standard; industry wrong: automotive not semiconductor"),
    (72, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Shortage' — should be weather"),
    (73, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not general"),
    (74, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not general"),
    (75, False, True,  True,  True,  True,  True,  "Category non-standard 'Investment delay / Capacity reduction'"),
    (76, True,  False, True,  True,  True,  True,  "Industry wrong: paper/packaging not general"),
    (77, True,  False, True,  True,  True,  True,  "Industry wrong: manufacturing not logistics"),
    (78, True,  True,  True,  True,  True,  True,  "All correct"),
    (79, True,  True,  True,  True,  True,  True,  "All correct"),
    (80, False, False, True,  True,  True,  True,  "Category non-standard; industry wrong: manufacturing not logistics"),
    (81, False, False, True,  True,  True,  True,  "Category non-standard 'Market Shift'; industry wrong: apparel not logistics"),
    (82, True,  False, True,  True,  True,  False, "Industry wrong: logistics not automotive; signal wrong: Propagation not Trigger"),
    (83, True,  False, True,  True,  True,  True,  "Industry wrong: food not energy"),
    (84, True,  True,  True,  True,  True,  True,  "All correct"),
    (85, False, False, True,  True,  True,  True,  "Category non-standard 'Demand Shock'; industry wrong: apparel not general"),
    (86, False, True,  True,  True,  True,  False, "Category non-standard 'Market Shift'; signal wrong: record exports = Recovery not Propagation"),
    (87, False, True,  True,  True,  True,  True,  "Category non-standard 'Biological Contamination'"),
    (88, True,  True,  True,  True,  True,  True,  "All correct"),
    (89, True,  True,  True,  True,  True,  True,  "All correct"),
    (90, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Shortage'"),
    (91, False, True,  True,  True,  True,  True,  "Category non-standard 'Supply Shortage'"),
    (92, False, False, True,  True,  True,  True,  "Category non-standard 'Market Shift'; industry wrong: manufacturing not logistics"),
    (93, False, True,  True,  True,  True,  True,  "Category non-standard 'Regulatory/Operational'"),
]

records = []
for llm, label in zip(llm_outputs, manual_labels):
    sid, cat_ok, ind_ok, reg_ok, sev_ok, prop_ok, sig_ok, notes = label
    records.append({
        "sample_id": sid,
        "headline": llm["headline"],
        "llm_category": llm["disruption_category"],
        "llm_industry": llm["affected_industry"],
        "llm_region": llm["region"],
        "llm_severity": llm["severity_score"],
        "llm_propagation": llm["propagation_risk"],
        "llm_signal": llm["signal_type"],
        "category_correct": cat_ok,
        "industry_correct": ind_ok,
        "region_correct": reg_ok,
        "severity_correct": sev_ok,
        "propagation_correct": prop_ok,
        "signal_correct": sig_ok,
        "notes": notes,
    })

df = pd.DataFrame(records)
total = len(df)

fields = [
    ("disruption_category", "category_correct"),
    ("affected_industry",   "industry_correct"),
    ("region",              "region_correct"),
    ("severity_score",      "severity_correct"),
    ("propagation_risk",    "propagation_correct"),
    ("signal_type",         "signal_correct"),
]

summary_rows = []
for field, col in fields:
    correct = int(df[col].sum())
    wrong   = total - correct
    acc     = round((correct / total) * 100, 1)
    status  = "PASS" if acc >= 80 else "FAIL"
    summary_rows.append({"field": field, "correct": correct, "wrong": wrong,
                          "total": total, "accuracy_pct": acc, "status": status})

summary = pd.DataFrame(summary_rows)
df.to_csv(f"{OUTPUT_DIR}/validation_results.csv", index=False)
summary.to_csv(f"{OUTPUT_DIR}/validation_summary.csv", index=False)

print("\n" + "="*65)
print("  LLM EXTRACTION VALIDATION REPORT — 93 Samples")
print("="*65)
print(f"\n{'Field':<25} {'Correct':>8} {'Wrong':>7} {'Accuracy':>10}  Status")
print("-"*65)
for _, row in summary.iterrows():
    flag = "✅" if row["status"] == "PASS" else "❌"
    print(f"{row['field']:<25} {row['correct']:>8} {row['wrong']:>7} {row['accuracy_pct']:>9}%  {flag} {row['status']}")

all_cols = [c for _, c in fields]
overall = round(df[all_cols].values.mean() * 100, 1)
print("-"*65)
print(f"{'OVERALL ACCURACY':<25} {'':>15} {overall:>9}%")

fail_fields = summary[summary["status"] == "FAIL"]
if not fail_fields.empty:
    print("\n" + "="*65)
    print("  FIELDS BELOW 80% — Tell Member B to fix these")
    print("="*65)
    for _, row in fail_fields.iterrows():
        print(f"\n  ❌ {row['field'].upper()} — {row['accuracy_pct']}% ({row['wrong']} wrong out of {total})")
    print("""
  PROMPT FIXES FOR MEMBER B:
  ──────────────────────────────────────────────────────────
  1. DISRUPTION_CATEGORY (biggest problem):
     LLM is inventing free-text labels like 'Market Shift',
     'Supply Shortage', 'Equipment Shortage', 'Demand Shock',
     'Biological Contamination', 'Logistics Failure' etc.
     
     FIX — Add this to the prompt exactly:
     "disruption_category MUST be one of these values only:
      geopolitical, trade_policy, labor, weather, factory,
      port, pandemic, regulatory, economic, infrastructure_failure,
      natural_disaster, component_shortage, cyber
      Do NOT create new category names. Choose the closest match."

  2. AFFECTED_INDUSTRY (second biggest problem):
     LLM uses 'general' too broadly and misassigns industry.
     Common errors:
       - Port/shipping events → logistics (not automotive)
       - Garment/textile     → apparel (not general)  
       - Steel/chemical plant → manufacturing (not energy)
       - Copper/lithium mine  → mining (not general)
       - iPhone/laptop        → electronics (not general)

     FIX — Add enum + rule to prompt:
     "affected_industry MUST be one of:
      semiconductor, automotive, logistics, food, energy,
      pharmaceutical, apparel, agriculture, electronics,
      chemical, manufacturing, mining, aerospace, general
      Only use 'general' if truly no specific industry applies."

  3. REGION:
     'unknown' used when region IS clear from headline.
     e.g. 'TSMC Fab 14' → Taiwan; 'monsoon floods' → South Asia

     FIX: "If any country or region is mentioned or strongly
      implied, always specify it. Only use 'unknown' if the
      headline gives absolutely no geographic information."

  4. SIGNAL_TYPE (minor — 3 errors):
     - Declining orders = Precursor not Amplifier
     - Government policy reaction = Response not Amplifier  
     - Positive/recovery events = Recovery not Propagation

     FIX — Add definitions:
     "Precursor = early warning before disruption
      Trigger = direct cause of disruption
      Amplifier = worsens an existing disruption
      Propagation = downstream effect in another sector/region
      Response = policy or government reaction
      Recovery = situation improving or returning to normal"
""")

print(f"\nSaved → {OUTPUT_DIR}/validation_results.csv")
print(f"Saved → {OUTPUT_DIR}/validation_summary.csv\n")