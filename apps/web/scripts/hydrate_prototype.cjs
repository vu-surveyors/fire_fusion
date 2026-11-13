const fs = require('fs');
const path = require('path');

const prototypePath = path.resolve('apps/web/public/resources/FireFusion_Desktop_Prototype.html');
const docPrototypePath = path.resolve('doc/FireFusion_Desktop_Prototype.html');
const demoPath = path.resolve('apps/web/public/resources/data/demo.json');

const demoData = JSON.parse(fs.readFileSync(demoPath, 'utf8'));
const calHarm = demoData.data.calendar.harmonised;
const calRaw = demoData.data.calendar.raw;
const rawMap = new Map(calRaw.map(r => [r.date, r.count]));
const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fullMonthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];

// Convert all 552 calendar dates
const dates = calHarm.map(c => {
  const [y, m, day] = c.date.split('-');
  return {
    id: c.date,
    label: `${day} ${monthNames[Number(m)-1]} ${y}`,
    raw: rawMap.get(c.date) || c.count,
    harm: c.count,
    int: [c.lo, c.hi],
    ok: c.count > 0
  };
});

// Convert all clusters with coordinate projections (x, y between 5 and 95)
const clusters = Object.values(demoData.data.clusters).map(c => {
  const lat = c.centroid.lat;
  const lon = c.centroid.lon;
  // Bounding box: lat 20.5 - 26.5, lon 88.0 - 92.8
  const x = Math.max(5, Math.min(95, Math.round(((lon - 88.0) / 4.8) * 100)));
  const y = Math.max(5, Math.min(95, Math.round((1 - (lat - 20.5) / 6.0) * 100)));
  const nModis = c.summary?.n_modis || 0;
  const nViirs = c.summary?.n_viirs || 0;
  const sensors = (nModis > 0 && nViirs > 0) ? 'MODIS + VIIRS' : (nViirs > 0 ? 'VIIRS' : 'MODIS');
  const conf = c.event_score >= 0.8 ? 'High' : (c.event_score >= 0.4 ? 'Nominal' : 'Low');
  return {
    id: c.cluster_id,
    date: c.local_date,
    x, y,
    sensors,
    modis: nModis,
    viirs: nViirs,
    frp: Math.round((c.summary?.max_frp || 0) * 10) / 10,
    confidence: conf,
    cor: Boolean(c.corroborated),
    raw: nModis + nViirs,
    lat: Math.round(lat * 10000) / 10000,
    lon: Math.round(lon * 10000) / 10000
  };
});

// Distinct months across all dates
const distinctMonths = [...new Set(dates.map(x => x.id.slice(0, 7)))].sort();
const calMonths = distinctMonths.map(ym => {
  const [y, m] = ym.split('-').map(Number);
  const start = new Date(y, m - 1, 1).getDay();
  const days = new Date(y, m, 0).getDate();
  return { id: ym, label: `${fullMonthNames[m - 1]} ${y}`, start, days };
});

const methods = [
  ['01','What FireFusion is','FireFusion brings satellite fire detections into one clear activity record.'],
  ['02','Observation vs. event','Raw observations remain visible. Harmonized events group related same-day detections.'],
  ['03','Source boundary','Results reflect the selected workspace and its available records.'],
  ['04','Harmonization workflow','Normalisation, clustering and validation remain separate stages.'],
  ['05','Known limitations','This is not a wildfire prediction tool. It does not model fire spread, danger, or evacuation routes.']
];

console.log(`Generated ${dates.length} dates, ${clusters.length} clusters, and ${calMonths.length} months.`);

function updatePrototypeFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');

  // Replace DATA
  const newDATA = `let DATA=${JSON.stringify({ dates, clusters, methods })};`;
  content = content.replace(/const DATA=\{dates:\[.*?methods:\[.*?\]\};/s, newDATA);

  // Replace S initialization
  const oldS = `const S={view:'overview',date:'2026-03-15',filters:new Set(['High','Nominal','Low']),cluster:null,valid:'idle',validStep:0,validationToken:0,calMonth:'2026-03',legendOpen:false,calDetails:true,density:'comfortable',summaryPulse:false};`;
  const newS = `const S={view:'overview',date:'2025-03-25',filters:new Set(['High','Nominal','Low']),cluster:'CL_2025-03-25_0131',valid:'idle',validStep:0,validationToken:0,calMonth:'2025-03',legendOpen:false,calDetails:true,density:'comfortable',summaryPulse:false};`;
  content = content.replace(oldS, newS);

  // Replace CAL_MONTHS
  const oldCalMonths = /const CAL_MONTHS=\[\{id:'2026-01'.*?\}\];/;
  const newCalMonths = `let CAL_MONTHS=${JSON.stringify(calMonths)};`;
  content = content.replace(oldCalMonths, newCalMonths);

  // Replace today in calendar()
  content = content.replace("today='2026-03-15'", "today='2026-12-31'");
  content = content.replace("CAL_MONTHS[2]", "CAL_MONTHS.find(x=>x.id==='2025-03')||CAL_MONTHS[0]");

  // Add updateEmberMap function and trigger in setDate, setView, and after render
  if (!content.includes('function updateEmberMap(')) {
    const emberMapSyncCode = `
function updateEmberMap(){
  try {
    const frame = document.getElementById('ffEmberFrame');
    if (!frame) return;
    const emberWin = frame.contentWindow;
    if (!emberWin || !emberWin.FireMapPrototype) {
      frame.onload = () => updateEmberMap();
      return;
    }
    const dateClusters = C();
    const emberClusters = dateClusters.map(c => ({
      id: c.id,
      name: c.id,
      x: Math.max(0.05, Math.min(0.95, c.x / 100)),
      y: Math.max(0.05, Math.min(0.95, c.y / 100)),
      lat: c.lat || 23.0,
      lon: c.lon || 90.0,
      rotation: 0
    }));
    const emberObservations = [];
    dateClusters.forEach(c => {
      const n = Math.min(c.raw || 1, 15);
      for (let i = 0; i < n; i++) {
        const isModis = i < c.modis;
        const angle = (i / n) * 2 * Math.PI;
        const rad = 0.008 + 0.005 * (i % 3);
        emberObservations.push({
          clusterId: c.id,
          x: Math.max(0.02, Math.min(0.98, (c.x / 100) + Math.cos(angle) * rad)),
          y: Math.max(0.02, Math.min(0.98, (c.y / 100) + Math.sin(angle) * rad)),
          source: isModis ? 'MODIS' : 'VIIRS',
          confidence: (c.confidence || 'nominal').toLowerCase(),
          frp: Math.max(1, Math.round(c.frp / Math.max(1, n))),
          observedAt: (c.date || S.date) + 'T12:00:00Z'
        });
      }
    });
    if (emberClusters.length > 0) {
      emberWin.FireMapPrototype.setData({
        clusters: emberClusters,
        observations: emberObservations,
        updatedAt: S.date + 'T12:00:00+06:00'
      });
    }
  } catch(e) {
    console.warn('[FireFusion] Map update skipped:', e);
  }
}
async function hydrateFromBackend(){
  try {
    let payload = null;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/bundle', { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        const j = await res.json();
        if (j?.data?.calendar?.harmonised) payload = j.data;
      }
    } catch(e) {}
    if (!payload) {
      const res2 = await fetch('/resources/data/demo.json', { signal: AbortSignal.timeout(3000) });
      if (res2.ok) {
        const j2 = await res2.json();
        if (j2?.data?.calendar?.harmonised) payload = j2.data;
      }
    }
    if (payload && Array.isArray(payload.calendar?.harmonised)) {
      const rawMap = new Map((payload.calendar.raw || []).map(r => [r.date, r.count]));
      const mNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      DATA.dates = payload.calendar.harmonised.map(c => {
        const [y, m, da] = c.date.split('-');
        return {
          id: c.date,
          label: \`\${da} \${mNames[Number(m)-1]} \${y}\`,
          raw: rawMap.get(c.date) || c.count,
          harm: c.count,
          int: [c.lo, c.hi],
          ok: c.count > 0
        };
      });
      render();
      renderDates();
      updateEmberMap();
    }
  } catch(err) {
    console.warn('[FireFusion] Background hydration:', err);
  }
}
setTimeout(hydrateFromBackend, 500);
`;
    // Insert before </script>
    content = content.replace("render();sync(false);", `render();sync(false);${emberMapSyncCode}`);
  }

  // Hook updateEmberMap into setDate and setView
  content = content.replace("say(`${D().label} selected`);", "say(`${D().label} selected`);setTimeout(updateEmberMap,100);");
  content = content.replace("say(`${names[v]} opened`)", "say(`${names[v]} opened`);if(v==='map')setTimeout(updateEmberMap,150);");

  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully updated:', filePath);
}

updatePrototypeFile(prototypePath);
updatePrototypeFile(docPrototypePath);
