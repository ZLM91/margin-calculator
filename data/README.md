# Data Files for Matern'ella Video Dashboard

These JSON files are loaded by margin_calculator.html when localStorage is empty.

## How to update data

1. Open the deployed page in your browser (where localStorage has data)
2. Open Console (F12)
3. Run these two commands:

### Export US Ad Data
```js
var adData = JSON.parse(localStorage.getItem('maternella_video_data'));
var blob1 = new Blob([JSON.stringify(adData, null, 2)], {type: 'application/json'});
var a1 = document.createElement('a');
a1.href = URL.createObjectURL(blob1);
a1.download = 'us_ad_data.json';
a1.click();
```

### Export US Mapping
```js
var mapData = JSON.parse(localStorage.getItem('maternella_video_mapping_us'));
var cleanMap = {vidToCloud: mapData.mapping.vidToCloud, cloudToPerson: mapData.mapping.cloudToPerson};
var blob2 = new Blob([JSON.stringify(cleanMap, null, 2)], {type: 'application/json'});
var a2 = document.createElement('a');
a2.href = URL.createObjectURL(blob2);
a2.download = 'us_mapping.json';
a2.click();
```

4. Place both downloaded files in this `data/` directory
5. Commit and push to GitHub
