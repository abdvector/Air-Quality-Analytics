// Editable PowerPoint companion to presentation.tex. Run with the bundled artifact-tool runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const temp=path.join(root,'tmp/academic/pptx');
await fs.mkdir(temp,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#19334D',teal='#008A99',amber='#D88724',font='Arial';
function rect(s,x,y,w,h,fill,line='none') {
 return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1}});
}
function text(s,value,x,y,w,h,size=25,bold=false,color='#111111') {
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=value;a.text.insets=0;a.text.style={typeface:font,fontSize:size,bold,color};return a;
}
function slide(title,notes='') {
 const s=p.slides.add();s.background.fill='white';rect(s,0,0,1280,68,navy);
 text(s,title,23,16,1234,43,32,true,'#FFFFFF');
 text(s,`India Air Quality Analytics    ${p.slides.items.length}/10`,850,692,400,18,15,false,'#777777');
 s.speakerNotes.text=notes;return s;
}
function bullets(s,items,x,y,w,size=25,gap=56) {
 items.forEach((v,i)=>{text(s,'\u25b8',x,y+i*gap,22,30,size,true,teal);text(s,v,x+30,y+i*gap,w-30,gap-5,size);});
}
function block(s,title,body,y,h=110) {
 rect(s,44,y,1192,h,'#FBF4EB');rect(s,44,y,1192,34,amber);
 text(s,title,56,y+4,1160,28,24,true,'#FFFFFF');text(s,body,56,y+43,1160,h-48,24);
}
function table(s,values,x,y,w,h,widths) {
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 t.borders.assign({fill:'#C6CDD2',width:.6});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E7F1F2':'#FFFFFF';
  cell.text.style={typeface:font,fontSize:23,bold:r===0,color:'#111111'};
 }
 return t;
}
async function image(s,name,x,y,w,h) {
 const b=await fs.readFile(path.join(root,'docs/assets',name+'.jpg'));
 s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/jpeg',alt:name.replaceAll('_',' '),fit:'contain',position:{left:x,top:y,width:w,height:h}});
}

let s=slide('1. Introduction and Project Objectives','Source: project methodology and audited 2024 outputs. Data source: https://airquality.xkdr.org/. Historical batch analysis, no prediction.');
text(s,'Air Quality Analytics and Pollution Hotspot Detection in India',55,101,1160,48,29,true,navy);
text(s,'Study question',55,169,1160,35,26,true);
text(s,'Which monitoring stations repeatedly experience high pollution, and how much observed data supports the result?',55,212,1150,72,27);
bullets(s,['Analyze historical CPCB observations for the complete year 2024.','Select a pollutant, state, city and period in the dashboard.','Identify persistent hotspots and inspect monthly patterns.','Execute SQL in BigQuery and validate outputs independently.'],55,315,1160,25,56);
block(s,'Project contribution','Persistence screening with visible coverage, pollutant-specific averaging rules and explicit missing-data limitations.',568,110);

s=slide('2. Dataset and Big Data Scope','Source: data/india/audit/pipeline_run.json and download_manifest.json. XKDR Forum, CC BY 4.0, https://airquality.xkdr.org/. A record is one pollutant-station-time observation.');
table(s,[['Verified measure','Count'],['Monthly source files','12'],['All acquired source measurements','46,937,170'],['Selected CPCB measurements','27,021,875'],['Stations in the selected subset','533'],['Eligible pollutant-station-days','1,115,522'],['Combined station-days','165,652']],165,104,950,325,[670,280]);
bullets(s,['One record means one pollutant at one station and time.','PM2.5, PM10, NO2, SO2, O3, CO and NH3.','Source: XKDR Forum CPCB compilation, CC BY 4.0 [1].'],55,450,1160,24,43);
block(s,'Why BigQuery helps','Cloud SQL processes the measurements and returns filtered summaries. This demonstrates warehouse analytics without claiming a laptop cannot process the data.',576,108);

s=slide('3. System Design and Data Lifecycle','Source: implemented scripts, sql/bigquery and src/repository.py. DuckDB is an independent reference and is not a dashboard backend. No Airflow, Spark or Hadoop execution is claimed.');
const labels=['Original monthly files and station metadata','Python acquisition and bronze selection','BigQuery cleaning, windows and joins','Daily gold tables and filtered SQL','Streamlit dashboard / app.py'];
const nodes=labels.map((v,i)=>{let a=rect(s,55,110+i*108,670,73,'#E7F1F2',teal);a.text=v;a.text.insets=12;a.text.style={typeface:font,fontSize:25,color:navy};return a;});
for(let i=0;i<4;i++)s.shapes.connect(nodes[i],nodes[i+1],{fromSide:'bottom',toSide:'top',kind:'straight',line:{fill:teal,width:2},tail:{type:'arrow',length:'med',width:'med'}});
text(s,'Quality and provenance',790,110,425,40,27,true);text(s,'Checksums and row reconciliation. IST dates with unique UTC keys. No missing-value filling.',790,160,425,110,25);
text(s,'Independent check',790,304,425,40,27,true);text(s,'DuckDB reference outputs verify cloud results. It is a separate validation path.',790,354,425,110,25);
text(s,'Application access',790,498,425,40,27,true);text(s,'Read-only viewer credentials, bound parameters and a ten-minute cache.',790,548,425,100,25);

s=slide('4. Pollutant Rules and Combined Pollution Level','Sources: docs/METHODOLOGY.md, src/india_bands.py and https://ies.gov.in/arthapedia/concept/national-air-quality-index. The linked standards provide individual concentration references. Upper ozone bands use observed one-hour maxima above 208 and 748 ug/m3. Classification inputs round to eight decimals only. This is not official numeric AQI.');
table(s,[['Pollutant','Reference','Daily comparison'],['PM2.5 / PM10','60 / 100 ug/m3','24-hour mean'],['NO2 / SO2','80 / 80 ug/m3','24-hour mean'],['NH3','400 ug/m3','24-hour mean'],['O3','100 ug/m3','Highest eligible 8-hour mean'],['CO','2 mg/m3','Highest eligible 8-hour mean']],55,105,1170,270,[260,310,600]);
bullets(s,['Each day needs at least 16 valid hourly observations.','An 8-hour window needs six readings and stays within the IST day.','Combined level is the worst CPCB band, from 0 Good to 5 Severe.','Require at least three valid pollutants, including PM2.5 or PM10 [2].'],55,400,1160,24,43);
block(s,'Interpretation','Derived ordinal screening, not official numeric AQI. Missing pollutants can hide a worse band. O3 upper bands use the source table\u2019s one-hour convention.',576,108);

s=slide('5. Coverage and Persistent Hotspot Detection','Source: src/analytics.py, src/repository.py and output/india/coverage_sensitivity.csv. These are adjustable project screening definitions, not official hotspot classifications. Sensitivity varies both overall and monthly coverage.');
text(s,'Coverage (%)',55,120,540,40,29,true);text(s,'100 x valid days / calendar days',55,180,540,90,28);
text(s,'High-day fraction (%)',55,310,540,40,29,true);text(s,'100 x high days / valid days',55,370,540,90,28);
text(s,'Missing days never count as clean days.',55,488,545,65,25,true,navy);
text(s,'Default persistence rule',685,120,540,45,29,true);
bullets(s,['Overall day coverage at least 75%.','Counted months have at least 75% coverage.','At least 10% high days in a counted month.','At least three high-pollution months.'],685,193,540,25,81);
block(s,'Transparent project choices','PM2.5 persistent counts: 370 at 60% coverage, 342 at 75% and 250 at 90%. This changes eligibility, not measured air quality.',577,107);

s=slide('6. Dashboard Output: Pollution Hotspots','Actual dashboard screenshot: PM2.5, all states, 1 Jan to 31 Dec 2024, 75% coverage, 10% high days in at least 3 months. Source: output/india/station_rankings.csv. Map background attribution remains visible in screenshot. High fractions represent monitored stations, not whole cities.');
await image(s,'dashboard_map',75,93,1130,440);
bullets(s,['PM2.5: 416 coverage-eligible stations and 342 persistent hotspots.','Sector-51, Gurugram: 84.2% high days from 330 valid days.','Eleven eligible stations lack coordinates and remain in the ranking.'],55,548,1160,24,43);

s=slide('7. Dashboard Output: Monthly Patterns','Actual dashboard screenshot: default annual PM2.5 view, top 15 ranked stations. Low-coverage months are masked. This is a selected subset, not a representative national sample. A separate coverage heatmap is in the report. No causal or multi-year seasonal inference is established.');
await image(s,'dashboard_monthly',50,95,1180,430);
bullets(s,['Means of daily PM2.5 values for the top 15 ranked stations.','Blank cells fall below the coverage rule. A second heatmap shows coverage.','One year describes monthly differences, not recurring seasonality or causes.'],55,545,1160,24,43);

s=slide('8. Dashboard Output: Combined Level and Comparison','Actual combined-view screenshots, all states and full 2024, with default thresholds. Source: output/india/combined_rankings.csv and app.py. Combined high days mean level >=3, whereas individual high days exceed a pollutant benchmark. Score is ordinal, not official numeric AQI.');
text(s,'432 coverage-eligible stations and 222 persistent hotspots',55,100,1160,42,28,true,navy);
await image(s,'dashboard_combined_plot',60,153,1160,430);
bullets(s,['Derived combined level from 0 Good to 5 Severe. Poor starts at level 3.','Daily details show available pollutants. Compare up to three stations and export CSV.'],55,602,1160,23,38);

s=slide('9. Results, Validation and Course Alignment','Sources: output/india/station_rankings.csv, output/india/verification.txt, data/india/audit/cloud_execution.json and dashboard_cloud_parity.json. Course: supplied ED547 syllabus. Results use default full-year coverage and persistence definitions. Four cloud-output parity checks use numeric tolerance 1e-8 and exact flags. Tests do not prove sensor accuracy or scientific validity of every assumption.');
text(s,'Default annual screening',55,102,510,40,27,true);
table(s,[['View','Eligible','Persistent'],['PM2.5','416','342'],['PM10','412','372'],['NO2','425','35'],['SO2','432','4'],['O3','421','167'],['CO','435','172'],['NH3','389','0']],55,156,510,382,[190,150,170]);
text(s,'Validation evidence',660,102,560,40,27,true);
bullets(s,['32 tests passed after cleanup.','Four cloud tables match the local reference.','Three dashboard aggregation scenarios match.'],660,165,560,25,76);
text(s,'ED547 connection',660,412,560,40,27,true);
text(s,'Modules IV and V: ETL, BigQuery, SQL and Python. Modules I and II: lifecycle, data quality and warehouse storage.',660,463,560,107,25);
block(s,'Verified execution','Real BigQuery jobs and processing records are retained. Hadoop, Spark and Airflow are not implemented. No controlled speed benchmark is claimed.',576,108);

s=slide('10. Conclusion, Limitations and References','References accessed 1 November 2026. [1] https://airquality.xkdr.org/ [2] https://ies.gov.in/arthapedia/concept/national-air-quality-index [3] https://docs.cloud.google.com/bigquery/docs/sandbox. Project results derive from retained audit and result files. All dashboard images are original captures of this project.');
text(s,'Conclusion',55,98,1160,35,27,true);
text(s,'Large-scale cloud processing linked to station-level evidence, coverage-aware persistence and reproducible outputs.',55,143,1160,70,26);
text(s,'Limitations',55,235,1160,35,27,true);
bullets(s,['Historical 2024 data only. No prediction or attribution of causes.','Uneven monitoring, missing pollutants and 53 missing-coordinate stations.','Derived combined level and adjustable project thresholds.','Sandbox tables expire after 60 days. Internet and credentials are required [3].'],55,284,1160,24,43);
text(s,'References',55,476,1160,35,26,true);
text(s,'[1] XKDR Forum. India Air Quality Database. https://airquality.xkdr.org/\n[2] Indian Economic Service. National Air Quality Index.\n     https://ies.gov.in/arthapedia/concept/national-air-quality-index\n[3] Google Cloud. BigQuery sandbox. https://docs.cloud.google.com/bigquery/docs/sandbox',55,523,1160,145,19);

for (const [i,s] of p.slides.items.entries()){
 const blob=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(temp,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidate=path.join(temp,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
const skill=process.env.BDA_PRESENTATION_SKILL || path.join(process.env.USERPROFILE,'.codex/plugins/cache/openai-primary-runtime/presentations/26.1029.11837/skills/presentations');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(here,'India_Air_Quality_Deck.pptx'),explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[2,4,9],requiredNativeChartOwnerSlides:[],pythonExecutable:process.env.BDA_PYTHON || path.join(root,'.venv/Scripts/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','2','--require-native-table-slide','4','--require-native-table-slide','9'],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(temp,`validation-${Date.now()}.json`)});
console.log('Created editable 10-slide presentation');
