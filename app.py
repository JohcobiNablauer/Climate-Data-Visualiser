import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import copy


class ClimateApp:
    def __init__(self):
        self.file, self.file_name = None, None
        self.entry = None

        self.months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        self.AVG_TEMP, self. SUM_PRECIP = None, None
        self.N_LABELS, self.P_LABELS = [], []
        self.T_COL, self.P_COL = '#d73027', ['#5e93d1', '#4363aa']

        self.decorations = {
            'Name': '🏷️',
            'Station': '🛰️',
            'Land': '🌍',
            'Höhe': '⛰️',
            'Lage': '📍',
            'Temperaturen': '🌡️',
            'Niederschläge': '🌧️'
        }

    def run(self):
        st.title('Klimadaten-Dashboard')
        self._select_source()

        if self.file_name:
            self._select_option()

        if self.entry:
            self.data_section()

            self.AVG_TEMP = round(sum(self.entry['Temperaturen']) / 12, 1)
            self.SUM_PRECIP = int(sum(self.entry['Niederschläge']))

            self.table_section()
            self.diagram_section()


    def data_section(self):
        st.markdown('---')
        st.header('Parameter')

        for key, value in self.entry.items():
            if key in ['Temperaturen', 'Niederschläge']:
                st.markdown(f'{self.decorations[key]} **{key}**')
                cols = st.columns([1] * 12)
                for i, v in enumerate(value):
                    updated = cols[i].text_input(label=key, placeholder=v, label_visibility='collapsed', key=f'{key}{i}')
                    if updated:
                        try:
                            self.entry[key][i] = round(float(updated), 0 if key == 'Niederschläge' else 1)
                        except ValueError:
                            st.error(f'Ungültige {key}: {updated} für {key} an Position {i + 1} ({self.months[i]})')
            else:
                col1, col2 = st.columns([1,2])
                col1.markdown(f'{self.decorations[key]} **{key}**')
                
                updated = col2.text_input(label=key, placeholder=value, label_visibility='collapsed')
                if updated:
                    if key == 'Höhe' and isinstance(updated, (int, float)):
                        updated = int(updated)
                    self.entry[key] = updated
        
        cols = st.columns(3)
        self._edit_messages()
        for i, col in enumerate(cols):
            if col.button(['Speichern', 'Speichern unter', 'Löschen'][i]):
                self._edit_buttons(i)
        st.info('ℹ️ Das **Überschreiben** und **Löschen** von Datensätzen ist **unumkehrbar**!')

    def table_section(self):
        st.markdown('---')
        st.header('Tabelle')
        df = pd.DataFrame({
            'Monat': self.months + [''],
            'Temperatur (in °C)': [round(t, 1) for t in self.entry['Temperaturen']] + ['∅ ' + str(self.AVG_TEMP)],
            'Niederschlag (in mm)': [int(p) for p in self.entry['Niederschläge']] + ['Σ ' + str(self.SUM_PRECIP)]
        })
        st.dataframe(df.set_index('Monat').transpose())
    
    def diagram_section(self):
        st.markdown('---')
        st.header('Klimadiagramm')

        self._get_labels()

        t_vals = [self.entry['Temperaturen'][-1], *self.entry['Temperaturen'], self.entry['Temperaturen'][0]]
        p_vals = self.entry['Niederschläge']
        ticks = [-0.5] + [0.5 + i for i in range(12)] + [12.5]
        
        fig = go.Figure()

        months = ['', *self.months, '']
        customdata = [[t_val, months[i]] for i, t_val in enumerate(t_vals)]
        temp_config = {'mode': 'lines', 'line': dict(color=self.T_COL), 'name': 'Temperatur', 'customdata': customdata, 'hovertemplate': 'Temperatur: %{customdata[0]}°C<br>Monat: %{customdata[1]}<extra></extra>'}

        fig.add_trace(go.Scatter(x=ticks, y=[self._scale(t_val * 2) for t_val in t_vals], **temp_config))
        fig.add_trace(go.Scatter(x=[0], y=[0], xaxis='x2', yaxis='y2', marker=dict(opacity=0), hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=[0], y=[0], xaxis='x2', yaxis='y3', marker=dict(opacity=0), hoverinfo='skip'))
        
        for i, p_val in enumerate(p_vals):
            get_config = lambda v, name, color, custom_v: {
                'x': [ticks[i + 1]],
                'y': [v],
                'name': name,
                'marker_color': self.P_COL[color],
                'width': 0.5,
                'customdata': [[custom_v, self.months[i]]],
                'hovertemplate': 'Niederschlag: %{customdata[0]} mm<br>Monat: %{customdata[1]}<extra></extra>'
            }
            scaled = self._scale(p_val)
            border = self._scale(100)
            if p_val > 100:
                high_config = get_config(scaled, 'Niederschlag > 100', 1, p_val)
                fig.add_trace(go.Bar(**high_config))
            low_config = get_config(min([scaled, border]), 'Niederschlag <= 100', 0, min([p_val, 100]))
            fig.add_trace(go.Bar(**low_config))

        temp_labels = self.N_LABELS + [i // 2 if i <= 100 else '' for i in self.P_LABELS]
        precip_labels = [''] * len(self.N_LABELS) + self.P_LABELS

        low, high = -len(self.N_LABELS),  len(self.P_LABELS)
        y_0 = abs(low) / (high - low)

        font_size, font_color = 14, 'black'
        line_width, line_color = 2, 'black'
        grid_width, g_major_color, g_minor_color = 1, 'gray', 'lightgray'
        xg_minor, xg_major, yg_minor, yg_major = True, True, True, True

        line_config = {'linewidth': line_width, 'linecolor': line_color, 'mirror': True}
        tick_config = {'size': font_size, 'color': font_color}
        annotations_config = {'y': high - 0.5, 'xref': 'x', 'yref': 'y', 'yanchor': 'middle', 'align': 'center', 'valign': 'middle', 'showarrow': False, 'bgcolor': 'white'}

        fig.update_layout(
            xaxis1=dict(**line_config, showgrid=xg_minor, gridwidth=grid_width, gridcolor=g_minor_color, position=y_0,
                       range=[0, 12], tickvals=ticks[1:], ticktext=self.months, tickfont=tick_config,
                       title='Monat', title_font=dict(size=font_size+4, color=font_color)),
            xaxis2=dict(showgrid=xg_major, gridwidth=grid_width, gridcolor=g_major_color, overlaying='x',
                       range=[0.5, 12.5], showticklabels=False, tickvals=ticks[1:]),
            yaxis=dict(**line_config, showgrid=yg_major, gridwidth=grid_width, gridcolor=g_major_color, position=0, side='left',
                       range=[low, high], tickvals=list(range(low, high, 1)), ticktext=temp_labels, tickfont=tick_config,
                       title='Temperatur in °C', title_font=dict(size=font_size+4, color=self.T_COL)),
            yaxis2=dict(**line_config, showgrid=False, position=1, overlaying='y', side='right',
                        range=[low, high], tickvals=list(range(low, high, 1)), ticktext=precip_labels, tickfont=tick_config,
                        title='Niederschlag in mm', title_font=dict(size=font_size+4, color=self.P_COL[1])),
            yaxis3=dict(showgrid=yg_minor, gridwidth=grid_width, gridcolor=g_minor_color, position=1, overlaying='y', side='right',
                         range=[low, high], showticklabels=False, tickvals=[0.5 + i + low for i in range(-low + high)]),

            annotations=[
                go.layout.Annotation(**annotations_config, x=0.02, xanchor='left',
                                     text=f'{self.entry['Station']}/{self.entry['Land']}, {self.entry['Höhe']} m', font=tick_config),
                go.layout.Annotation(**annotations_config, x=6, xanchor='center',
                                     text=self.entry['Lage'], font=tick_config),
                go.layout.Annotation(**annotations_config, x=9, xanchor='center',
                                     text=f'{self.AVG_TEMP} °C'.replace('.', ','), font=tick_config),
                go.layout.Annotation(**annotations_config, x=11.98, xanchor='right',
                                     text=f'{self.SUM_PRECIP} mm'.replace('.', ','), font=tick_config)
                ],

            barmode='overlay',
            dragmode=False,
            showlegend=False,
            template='plotly_white',
            height=(len(self.N_LABELS) + len(self.P_LABELS)) *50 + 100
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'doubleClick': 'reset'})
        
        resolutions = ['niedrig', 'mittel', 'hoch']
        choice = st.selectbox('Auflösung: ', resolutions, 1)
        st.download_button(
            label='Als Bild herunterladen',
            data=fig.to_image(format='png', scale=resolutions.index(choice) + 1),
            file_name='Klimadiagramm.png',
            mime='image/png'
        )


    def _select_source(self):
        file = st.file_uploader('Datei einfügen: (Standardname: "Klimadaten.json")', type='json')
        if file:
            if st.session_state.get('file_name'):
                self.file = st.session_state.get('file')
                self.file_name = st.session_state.get('file_name')
            else:
                self.file = json.load(file)
                self.file_name = file.name
        else:
            self.file, self.file_name = None, None
            sample = [
                {'Name': 'Musterdatensatz',
                 'Station': 'New York City',
                 'Land': 'USA',
                 'Höhe': '20',
                 'Lage': '40°N/74°W',
                 'Temperaturen': [-1.0, 0.0, 4.1, 10.4, 16.0, 21.3, 24.5, 23.6, 20.1, 13.7, 7.7, 2.5],
                 'Niederschläge': [86, 78, 106, 92, 92, 103, 105, 106, 95, 97, 76, 103]
                }
            ]
            
            st.info("Keine Datei? Musterdatei **herunterladen** und oben **einfügen**:")
            st.download_button(label=f'Musterdatei herunterladen', data=json.dumps(sample, indent=2, ensure_ascii=False), file_name='Klimadaten.json', mime='application/json', key='1')
        
        if self.file_name:
            col1, col2 = st.columns([1, 3])
            col1.download_button(label=f'Herunterladen', data=json.dumps(self.file, indent=2, ensure_ascii=False), file_name=self.file_name, mime='application/json', key='download')
            col2.warning('⚠️ Änderungen jedes Datensatzes vorher speichern!')

    def _select_option(self):
        actions = ['Datensatz laden', 'Datensatz erstellen']
        options = actions if self.file else [actions[-1]]
        index = options.index(st.session_state.sel_action) if st.session_state.get('sel_action') in options else None
        
        if st.session_state.get('load'):
            st.session_state.sel_action = options[0]
            st.session_state.load = False
            st.rerun()
        
        sel_action = st.radio('Wählen Sie eine Aktion:', options, index, key='sel_action')
        if st.session_state.sel_action in options:
            if sel_action == 'Datensatz laden':
                sel_name = st.selectbox('Wählen Sie einen Datensatz:', [entry['Name'] for entry in self.file], index=st.session_state.name if 'name' in st.session_state else None)
                if sel_name:
                    self.entry = copy.deepcopy(next((entry for entry in self.file if entry['Name'] == sel_name), None))

            else:
                self.entry = dict.fromkeys(['Name', 'Station', 'Land', 'Höhe', 'Lage'])
                self.entry['Temperaturen'] = [0] * 12
                self.entry['Niederschläge'] = [0] * 12

    def _edit_messages(self):
        if 'messages' in st.session_state:
            for msg in st.session_state.messages.get('success', []):
                st.success(msg)
            for msg in st.session_state.messages.get('error', []):
                st.error(msg)
            for msg in st.session_state.messages.get('warning', []):
                st.warning(msg)
        st.session_state.messages = {
                'success': [],
                'error': [],
                'warning': []
            }

    def _edit_buttons(self, action):
        name = self.entry.get('Name')
        index = next((i for i, e in enumerate(self.file) if e['Name'] == self.entry['Name']), None)

        def save():
            if index is not None:
                self.file[index].update(self.entry)
                st.session_state.messages['success'].append(f'✅ Datensatz **"{name}"** überschrieben.')
            else:
                st.session_state.messages['warning'].append('⚠️ "Speichern" überschreibt **ausgewählte** Datensätze. Für **neue** Einträge bitte "Speichern unter" wählen.')
        
        def save_as():
            if not name:
                st.session_state.messages['error'].append('❌ Bitte geben Sie einen Dateinamen ein.')
            elif any(d.get('Name') == name for d in self.file):
                st.session_state.messages['error'].append(f'❌ Name **"{name}"** bereits vergeben.')
            else:
                self.file.append(self.entry)
                st.session_state.messages['success'].append(f'✅ Datensatz **"{name}"** erstellt.')
                  
        def delete():
            if index is not None:
                match = next((d for d in self.file if d['Name'] == name), None)
                if match:
                    st.session_state.messages['success'].append(f'✅ Datensatz **"{name}"** gelöscht.')
                    self.file.remove(match)
                else:
                    st.session_state.messages['error'].append(f'Dateiname **{name}** nicht gefunden.')
            else:
                st.session_state.messages['error'].append('"Löschen" entfernt **ausgewählte** Datensätze. **Ungespeicherte** Datensätze können nicht gelöscht werden.')
        [save, save_as, delete][action]()
        self._update_session(len(self.file), action == 2)
    
    def _update_session(self, index, delete=False):
        st.session_state.file = self.file
        st.session_state.file_name = self.file_name

        if  delete and not index:
            st.session_state.pop('name', None)
            st.session_state.pop('load', None)
        else:
            st.session_state.name = index - 1
            st.session_state.load = True

        st.rerun()

    def _get_labels(self):
        t_max, t_min, p_max = max(self.entry['Temperaturen']), min(self.entry['Temperaturen']), max(self.entry['Niederschläge'])
        labels = [0]
        while labels[-1] <= max(t_max * 2, p_max):
            step = 20 if len(labels) < 6 else 100
            labels.append(labels[-1] + step)
        self.P_LABELS = labels
        self.N_LABELS = sorted(list(range(-10, int(t_min) - 10, -10))) if t_min < 0 else []

    def _scale(self, y):
        if y <= 100:
            return y / 20
        else:
            return 5 + (y - 100) / 100



if __name__ == '__main__':
    app = ClimateApp()
    app.run()
