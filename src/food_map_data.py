"""Approximate dining-area anchors, not individual restaurant locations.

Landmarks from © OpenStreetMap contributors, ODbL:
https://www.openstreetmap.org/copyright
"""
AREA_POINTS = {
    ('ams', 'Amsterdam Zuid'): (52.33872, 4.87134),  # https://www.openstreetmap.org/node/5252944882
    ('ams', 'Bos en Lommer・西區'): (52.37802, 4.8468),  # https://www.openstreetmap.org/way/46431760
    ('ams', 'De Pijp・Albert Cuyp'): (52.35523, 4.89178),  # https://www.openstreetmap.org/relation/7112728
    ('ams', 'Jordaan・Noordermarkt'): (52.37995, 4.88687),  # https://www.openstreetmap.org/way/7378497
    ('ams', 'Jordaan・安妮之家'): (52.37516, 4.88408),  # https://www.openstreetmap.org/way/601081859
    ('ams', 'Leidseplein'): (52.36396, 4.88276),  # https://www.openstreetmap.org/way/1231991755
    ('ams', 'Oost・Funenkade'): (52.36686, 4.92643),  # https://www.openstreetmap.org/way/146834049
    ('ams', 'Oost・Middenweg'): (52.34898, 4.93829),  # https://www.openstreetmap.org/way/46610976
    ('ams', 'Oud-West・De Hallen'): (52.36695, 4.8682),  # https://www.openstreetmap.org/way/94517266
    ('ams', 'Waterlooplein'): (52.36845, 4.90179),  # https://www.openstreetmap.org/relation/13239097
    ('ams', '中央車站'): (52.3789, 4.90058),  # https://www.openstreetmap.org/node/4290854847
    ('ams', '老城・Dam 廣場'): (52.37312, 4.89235),  # https://www.openstreetmap.org/way/94756489
    ('ams', '老城・九條街'): (52.3704, 4.88369),  # https://www.openstreetmap.org/way/7372742
    ('utr', '老城・運河'): (52.09104, 5.12033),  # https://www.openstreetmap.org/way/7010311
    ('dh', 'Haagse Markt'): (52.0644, 4.29932),  # https://www.openstreetmap.org/way/40581479
    ('dh', '市中心・Torenstraat'): (52.07855, 4.30476),  # https://www.openstreetmap.org/way/7477622
    ('lei', '老城・Pieterskerk'): (52.15762, 4.48785),  # https://www.openstreetmap.org/way/52966906
    ('rtm', 'Delfshaven 方向'): (51.9081, 4.44837),  # https://www.openstreetmap.org/relation/10459111
    ('rtm', 'Markthal・Blaak'): (51.92011, 4.48696),  # https://www.openstreetmap.org/way/437982193
    ('rtm', 'Witte de Withstraat'): (51.91552, 4.47678),  # https://www.openstreetmap.org/way/7515023
    ('rtm', '北區・Hofbogen'): (51.93193, 4.47117),  # https://www.openstreetmap.org/way/386754850
    ('rtm', '市中心・Rodezand'): (51.92057, 4.48192),  # https://www.openstreetmap.org/way/7522922
    ('bru', '老城・Begijnhof'): (51.20135, 3.22288),  # https://www.openstreetmap.org/way/243594039
    ('bru', '老城・Hoogstraat'): (51.20944, 3.22872),  # https://www.openstreetmap.org/way/3515194
    ('bru', '老城・Markt／Burg'): (51.20871, 3.2244),  # https://www.openstreetmap.org/relation/5301046
    ('bru', '老城・Simon Stevinplein'): (51.2065, 3.22259),  # https://www.openstreetmap.org/way/145419676
    ('bxl', 'Bourse・交易所'): (50.84793, 4.34909),  # https://www.openstreetmap.org/way/525590461
    ('bxl', 'Sainte-Catherine'): (50.85073, 4.34769),  # https://www.openstreetmap.org/relation/5617344
    ('bxl', '中央車站'): (50.84546, 4.35699),  # https://www.openstreetmap.org/node/3266203405
    ('bxl', '老城・大廣場'): (50.84673, 4.35241),  # https://www.openstreetmap.org/way/991425177
    ('kol', 'Heumarkt'): (50.935, 6.96138),  # https://www.openstreetmap.org/way/204177815
    ('kol', 'Rudolfplatz'): (50.93667, 6.93989),  # https://www.openstreetmap.org/way/1292031124
    ('kol', 'Zülpicher Platz'): (50.93069, 6.93995),  # https://www.openstreetmap.org/way/32011635
    ('kol', '大教堂・老城'): (50.9413, 6.95814),  # https://www.openstreetmap.org/way/4532022
    ('kol', '比利時區・Friesenstraße'): (50.94094, 6.94447),  # https://www.openstreetmap.org/way/4400204
    ('kol', '比利時區・Stadtgarten'): (50.94299, 6.93516),  # https://www.openstreetmap.org/way/87638259
    ('dus', 'Altstadt・老城'): (51.22585, 6.77223),  # https://www.openstreetmap.org/relation/1978678
    ('dus', 'Little Tokyo・日本街'): (51.22499, 6.78548),  # https://www.openstreetmap.org/way/458920543
    ('haa', '老城・Raaks'): (52.38206, 4.6306),  # https://www.openstreetmap.org/way/454671141
}
