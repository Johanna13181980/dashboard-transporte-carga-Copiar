import io, re, unicodedata
from pathlib import Path
from collections import Counter
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Dashboard | Transporte de carga',page_icon='🚚',layout='wide')
COLORS=['#2F6079','#64929C','#9CB8AE','#637C94','#B9C9CE']
px.defaults.template='plotly_white'
px.defaults.color_discrete_sequence=COLORS
st.markdown('''<style>.stApp{background:#F5F7FA}.block-container{padding-top:1.5rem;max-width:1500px}[data-testid="stMetric"]{background:white;border:1px solid #E2E9EF;padding:15px;border-radius:12px}h1,h2,h3{color:#20394D}</style>''',unsafe_allow_html=True)

def norm(v):
 s=str(v).lower().strip()
 return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')

def getcol(df,i):
 matches=[c for c in df if re.search(rf'pregunta\s*0?{i}\s*:',norm(c))]
 if len(matches)==1:return matches[0]
 keys={1:'vehiculos operativos',2:'anos lleva funcionando',3:'tipo de carga',4:'tecnologias ha implementado',5:'otras tecnologias',6:'nivel educativo',7:'personal ha recibido capacitacion',8:'nivel de conocimiento',9:'costos de implementar',10:'subsidios',11:'eficiencia operativa'}
 matches=[c for c in df if keys[i] in norm(c)]
 return matches[0] if len(matches)==1 else None

@st.cache_data
def read_excel(content):
 df=pd.read_excel(io.BytesIO(content))
 df.columns=[re.sub(r'\s+',' ',str(c)).strip() for c in df.columns]
 return df.dropna(how='all')

def label(v):return 'Sin respuesta' if pd.isna(v) or not str(v).strip() else str(v).strip()
def likert(v):
 m=re.match(r'^\s*([1-5])(?:[.,]0)?(?:\D|$)',str(v))
 return float(m.group(1)) if m else float('nan')

TECH={
 'GPS y rastreo':['gps y rastreo'],
 'Software de rutas':['software de gestion de rutas'],
 'Plataformas TMS/WMS':['plataformas de gestion logistica'],
 'Sensores IoT':['sensores iot'],
 'Aplicaciones móviles':['aplicaciones moviles'],
 'Mantenimiento':['sistemas de mantenimiento','mantenimiento predictivo'],
 'Telemetría avanzada':['telemetria avanzada'],
 'Monitoreo':['tecnologia de monitoreo','monitoreo de emisiones'],
}
def technologies(v):
 if pd.isna(v) or not str(v).strip():return []
 s=norm(v)
 # Preserve commas within known choices such as (TMS, WMS).
 found=[]; positions=[]
 for name,patterns in TECH.items():
  for pat in patterns:
   for match in re.finditer(r'(?<!\w)'+re.escape(pat),s):positions.append((match.start(),match.end(),name))
 positions.sort()
 for _,_,name in positions:
  if name not in found:found.append(name)
 if not positions:return ['Revisar: '+str(v).strip()]
 # Keep unknown segments visible for data quality review.
 residual=s[:positions[0][0]]
 for j,(_,end,_) in enumerate(positions):
  nxt=positions[j+1][0] if j+1<len(positions) else len(s)
  residual+=' '+s[end:nxt]
 residual=re.sub(r'\([^)]*\)',' ',residual).strip(' ,;')
 if residual and norm(residual) not in ['ninguna','no aplica']:
  for fragment in re.split(r'\s*[,;]\s*',residual):
   if fragment.strip():found.append('Revisar: '+fragment.strip())
 return list(dict.fromkeys(found))

def plot_counts(df,col,title,horizontal=False):
 counts=df[col].map(label).value_counts().rename_axis('Categoría').reset_index(name='Empresas')
 if horizontal:
  counts=counts.sort_values('Empresas')
  fig=px.bar(counts,x='Empresas',y='Categoría',orientation='h',text='Empresas',title=title)
 else:fig=px.bar(counts,x='Categoría',y='Empresas',text='Empresas',title=title)
 fig.update_traces(textposition='outside',marker_color=COLORS[0])
 fig.update_layout(height=max(330,len(counts)*42+100) if horizontal else 350,margin=dict(l=10,r=20,t=55,b=40),showlegend=False)
 st.plotly_chart(fig,use_container_width=True)

def donut(df,col,title):
 counts=df[col].map(label).value_counts().rename_axis('Categoría').reset_index(name='Empresas')
 fig=px.pie(counts,names='Categoría',values='Empresas',hole=.58,title=title,color_discrete_sequence=COLORS)
 fig.update_traces(textinfo='percent')
 fig.update_layout(height=360,margin=dict(l=5,r=5,t=55,b=45),legend=dict(orientation='h',y=-.18))
st.plotly_chart(fig, use_container_width=True, key="grafico_principal")
def heatmap(df,x,y,title):
 ct=pd.crosstab(df[x].map(label),df[y].map(label))
 if ct.empty:return
 fig=px.imshow(ct,text_auto=True,aspect='auto',title=title,color_continuous_scale=[[0,'#EAF1F2'],[1,'#2F6079']])
 fig.update_layout(height=390,margin=dict(l=20,r=20,t=55,b=65),xaxis_title='',yaxis_title='')
 st.plotly_chart(fig,use_container_width=True)

def scaleplot(df,col,title):
 counts=df[col].value_counts().reindex([1,2,3,4,5],fill_value=0)
 fig=px.bar(x=[str(i) for i in counts.index],y=counts.values,text=counts.values,title=title,labels={'x':'Escala Likert','y':'Empresas'})
 fig.update_traces(marker_color=COLORS[0],textposition='outside')
 fig.update_layout(height=350,margin=dict(l=15,r=20,t=55,b=40))
 st.plotly_chart(fig,use_container_width=True)

st.sidebar.header('🚚 Datos y filtros')
upload=st.sidebar.file_uploader('Cargue el Excel de respuestas',type='xlsx')
if upload:raw=upload.getvalue()
else:
 paths=[p for p in Path('.').glob('*.xlsx') if 'transporte' in norm(p.name) and 'tecnolog' in norm(p.name)]
 raw=paths[0].read_bytes() if paths else None
if raw is None:
 st.title('Dashboard de adopción tecnológica | Transporte de carga')
 st.info('Para comenzar, cargue el Excel de respuestas desde el panel izquierdo. También puede colocar el archivo Excel en la misma carpeta de app.py.')
 st.stop()
try:df=read_excel(raw)
except Exception as e:st.error(f'No se pudo leer el Excel: {e}');st.stop()
P={i:getcol(df,i) for i in range(1,12)}
required=[1,2,3,4,6,7,8,9,10,11]
missing=[i for i in required if not P[i]]
if missing:
 st.error('No se encontraron las preguntas: '+', '.join(map(str,missing)))
 with st.expander('Columnas encontradas'):st.write(df.columns.tolist())
 st.stop()
consent=[c for c in df if 'autorizacion' in norm(c) or 'consentimiento' in norm(c)]
if consent:df=df[df[consent[0]].map(lambda v:'autorizo' in norm(v))].copy()
if df.empty:st.warning('No se encontraron respuestas autorizadas.');st.stop()
for i in required:df[f'P{i}']=df[P[i]].map(label)
df['Tecnologías']=df[P[4]].map(technologies)
df['Cantidad tecnologías']=df['Tecnologías'].map(len)
df['Capacitación']=df[P[7]].map(lambda v:norm(v) in ['si','yes'])
df['Costo Likert']=df[P[9]].map(likert)
df['Eficiencia Likert']=df[P[11]].map(likert)
st.sidebar.subheader('Segmentaciones')
chosen={}
for i,name in [(1,'Tamaño de flota · P1'),(3,'Tipo de carga · P3'),(6,'Nivel educativo · P6')]:
 opts=sorted(df[f'P{i}'].unique().tolist())
 chosen[i]=st.sidebar.multiselect(name,opts,default=opts)
d=df[df['P1'].isin(chosen[1]) & df['P3'].isin(chosen[3]) & df['P6'].isin(chosen[6])].copy()
if d.empty:st.warning('Los filtros no tienen respuestas coincidentes.');st.stop()
n=len(d)
valid=d['P7'].map(lambda x:norm(x) in ['si','no']).sum()
cap=100*d['Capacitación'].sum()/valid if valid else float('nan')
st.title('Adopción tecnológica en empresas de transporte de carga')
st.caption('Observatorio empresarial · Análisis descriptivo · Los indicadores responden a los filtros seleccionados')
a,b,c,e,f=st.columns(5)
a.metric('Empresas',n)
b.metric('Con capacitación',f'{cap:.1f} %' if pd.notna(cap) else 'N/D')
c.metric('Mejora percibida',f'{d["Eficiencia Likert"].mean():.2f} / 5')
e.metric('Costos percibidos',f'{d["Costo Likert"].mean():.2f} / 5')
f.metric('Tecnologías / empresa',f'{d["Cantidad tecnologías"].mean():.2f}')
tabs=st.tabs(['Panorama','Empresas','Tecnologías','Capital humano','Costos y eficiencia','Datos'])
with tabs[0]:
 a,b=st.columns(2)
 with a:donut(d,'P1','P1 · Tamaño de flota');donut(d,'P3','P3 · Tipo de carga')
 with b:donut(d,'P2','P2 · Antigüedad empresarial');donut(d,'P7','P7 · Capacitación')
with tabs[1]:
 a,b=st.columns(2)
 with a:plot_counts(d,'P1','P1 · Vehículos operativos');donut(d,'P3','P3 · Tipo de carga')
 with b:plot_counts(d,'P2','P2 · Años de funcionamiento');heatmap(d,'P1','P3','Flota × carga')
with tabs[2]:
 counts=Counter(t for arr in d['Tecnologías'] for t in set(arr))
 if counts:
  t=pd.DataFrame(counts.items(),columns=['Tecnología','Empresas']).sort_values('Empresas')
  t['Porcentaje']=100*t['Empresas']/n
  fig=px.bar(t,x='Empresas',y='Tecnología',orientation='h',text='Empresas',color='Porcentaje',color_continuous_scale=[[0,'#B8CCD1'],[1,'#285C77']],title='P4 · Tecnologías implementadas')
  fig.update_traces(textposition='outside')
  fig.update_layout(height=max(420,48*len(t)+110),margin=dict(l=10,r=30,t=55,b=30))
  st.plotly_chart(fig,use_container_width=True)
  st.caption('Selección múltiple: los porcentajes pueden sumar más del 100 %.')
  a,b=st.columns(2)
  with a:plot_counts(d,'Cantidad tecnologías','Diversificación tecnológica')
  with b:heatmap(d,'P1','P7','Flota × capacitación')
  st.dataframe(t.sort_values('Empresas',ascending=False),hide_index=True,use_container_width=True)
  if any(x.startswith('Revisar:') for x in t['Tecnología']):st.warning('Revise las opciones tecnológicas no reconocidas antes de publicar.')
with tabs[3]:
 a,b=st.columns(2)
 with a:donut(d,'P6','P6 · Formación del responsable');plot_counts(d,'P8','P8 · Conocimiento tecnológico')
 with b:donut(d,'P7','P7 · Capacitación');heatmap(d,'P7','P8','Capacitación × conocimiento')
with tabs[4]:
 a,b=st.columns(2)
 with a:scaleplot(d,'Costo Likert','P9 · Costos de implementación');donut(d,'P10','P10 · Subsidios y apoyos')
 with b:scaleplot(d,'Eficiencia Likert','P11 · Mejora de eficiencia');heatmap(d.assign(Costo=d['Costo Likert'].map(label)),'P7','Costo','Capacitación × costos')
 valid=d.dropna(subset=['Costo Likert','Eficiencia Likert'])
 if not valid.empty:
  g=valid.groupby(['Costo Likert','Eficiencia Likert']).size().reset_index(name='Empresas')
  fig=px.scatter(g,x='Costo Likert',y='Eficiencia Likert',size='Empresas',color='Empresas',size_max=46,title='Asociación descriptiva entre percepciones')
  fig.update_xaxes(dtick=1,range=[.5,5.5]);fig.update_yaxes(dtick=1,range=[.5,5.5])
  st.plotly_chart(fig,use_container_width=True)
with tabs[5]:
 sensitive=['correo','email','nombre','telefono','cedula','documento de identidad','direccion','marca temporal']
 export=[c for c in df.columns if not c.startswith('P') or c in df.columns[:0]]
 # Only original columns, excluding likely identifiers.
 export=[c for c in read_excel(raw).columns if c in d.columns and not any(term in norm(c) for term in sensitive)]
 safe=d[export].copy()
 st.dataframe(safe,hide_index=True,use_container_width=True)
 st.download_button('Descargar CSV filtrado',safe.to_csv(index=False,sep=';').encode('utf-8-sig'),'respuestas_filtradas.csv','text/csv')
 with st.expander('Diccionario de preguntas'):st.dataframe(pd.DataFrame([{'Pregunta':i,'Columna':P[i]} for i in required]),hide_index=True)
st.divider()
st.caption('Fuente: encuesta a empresas de transporte de carga. Muestra no probabilística; resultados descriptivos. Las escalas Likert reflejan percepciones, no efectos causales.')
