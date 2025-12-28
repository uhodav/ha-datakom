class DatakomControllerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  render() {
    if (!this._config) return;

    this.innerHTML = `
      <style>
        .editor-container {
          padding: 16px;
        }
        .section {
          margin-bottom: 24px;
        }
        .section-title {
          font-weight: 500;
          margin-bottom: 12px;
          color: var(--primary-text-color);
        }
        .input-group {
          margin-bottom: 16px;
        }
        .input-label {
          display: block;
          margin-bottom: 4px;
          font-size: 14px;
          color: var(--secondary-text-color);
        }
        ha-textfield {
          width: 100%;
        }
        .add-button {
          margin-top: 8px;
        }
        .item-editor {
          background: var(--secondary-background-color);
          padding: 12px;
          margin-bottom: 8px;
          border-radius: 4px;
          position: relative;
        }
        .remove-button {
          position: absolute;
          top: 8px;
          right: 8px;
          cursor: pointer;
          color: var(--error-color);
        }
      </style>

      <div class="editor-container">
        <!-- Basic Settings -->
        <div class="section">
          <div class="section-title">Основные настройки</div>
          <div class="input-group">
            <label class="input-label">Модель контроллера</label>
            <ha-textfield
              .value="${this._config.model || 'D 500'}"
              @input="${(e) => this._valueChanged('model', e.target.value)}"
            ></ha-textfield>
          </div>
          <div class="input-group">
            <label class="input-label">Заголовок дисплея</label>
            <ha-textfield
              .value="${this._config.display_title || 'GEN PHASE VOLTAGES'}"
              @input="${(e) => this._valueChanged('display_title', e.target.value)}"
            ></ha-textfield>
          </div>
        </div>

        <!-- Status Indicators -->
        <div class="section">
          <div class="section-title">Статусные индикаторы (слева)</div>
          <div id="status-indicators">
            ${this.renderStatusIndicatorsEditor()}
          </div>
          <mwc-button class="add-button" @click="${() => this.addStatusIndicator()}">
            Добавить индикатор
          </mwc-button>
        </div>

        <!-- Display Values -->
        <div class="section">
          <div class="section-title">Значения на дисплее</div>
          <div id="display-values">
            ${this.renderDisplayValuesEditor()}
          </div>
          <mwc-button class="add-button" @click="${() => this.addDisplayValue()}">
            Добавить значение
          </mwc-button>
        </div>

        <!-- Side Indicators -->
        <div class="section">
          <div class="section-title">Боковые индикаторы (справа)</div>
          <div id="side-indicators">
            ${this.renderSideIndicatorsEditor()}
          </div>
          <mwc-button class="add-button" @click="${() => this.addSideIndicator()}">
            Добавить индикатор
          </mwc-button>
        </div>

        <!-- Control Buttons -->
        <div class="section">
          <div class="section-title">Кнопки управления</div>
          <div id="control-buttons">
            ${this.renderControlButtonsEditor()}
          </div>
        </div>
      </div>
    `;
  }

  renderStatusIndicatorsEditor() {
    const indicators = this._config.status_indicators || [];
    return indicators.map((indicator, index) => `
      <div class="item-editor">
        <span class="remove-button" data-index="${index}" data-type="status">×</span>
        <div class="input-group">
          <label class="input-label">Метка</label>
          <ha-textfield
            .value="${indicator.label || ''}"
            @input="${(e) => this.updateStatusIndicator(index, 'label', e.target.value)}"
          ></ha-textfield>
        </div>
        <div class="input-group">
          <label class="input-label">Сенсор (entity)</label>
          <ha-entity-picker
            .hass="${this._hass}"
            .value="${indicator.entity || ''}"
            @value-changed="${(e) => this.updateStatusIndicator(index, 'entity', e.detail.value)}"
          ></ha-entity-picker>
        </div>
        <div class="input-group">
          <label class="input-label">Цвет LED</label>
          <ha-select
            .value="${indicator.color || 'red'}"
            @selected="${(e) => this.updateStatusIndicator(index, 'color', e.target.value)}"
          >
            <mwc-list-item value="red">Красный</mwc-list-item>
            <mwc-list-item value="green">Зеленый</mwc-list-item>
            <mwc-list-item value="yellow">Желтый</mwc-list-item>
          </ha-select>
        </div>
      </div>
    `).join('');
  }

  renderDisplayValuesEditor() {
    const values = this._config.display_values || [];
    return values.map((value, index) => `
      <div class="item-editor">
        <span class="remove-button" data-index="${index}" data-type="display">×</span>
        <div class="input-group">
          <label class="input-label">Метка</label>
          <ha-textfield
            .value="${value.label || ''}"
            @input="${(e) => this.updateDisplayValue(index, 'label', e.target.value)}"
          ></ha-textfield>
        </div>
        <div class="input-group">
          <label class="input-label">Сенсор (entity)</label>
          <ha-entity-picker
            .hass="${this._hass}"
            .value="${value.entity || ''}"
            @value-changed="${(e) => this.updateDisplayValue(index, 'entity', e.detail.value)}"
          ></ha-entity-picker>
        </div>
      </div>
    `).join('');
  }

  renderSideIndicatorsEditor() {
    const indicators = this._config.side_indicators || [];
    return indicators.map((indicator, index) => `
      <div class="item-editor">
        <span class="remove-button" data-index="${index}" data-type="side">×</span>
        <div class="input-group">
          <label class="input-label">Метка</label>
          <ha-textfield
            .value="${indicator.label || ''}"
            @input="${(e) => this.updateSideIndicator(index, 'label', e.target.value)}"
          ></ha-textfield>
        </div>
        <div class="input-group">
          <label class="input-label">Сенсор (entity)</label>
          <ha-entity-picker
            .hass="${this._hass}"
            .value="${indicator.entity || ''}"
            @value-changed="${(e) => this.updateSideIndicator(index, 'entity', e.detail.value)}"
          ></ha-entity-picker>
        </div>
        <div class="input-group">
          <label class="input-label">Цвет LED</label>
          <ha-select
            .value="${indicator.color || 'green'}"
            @selected="${(e) => this.updateSideIndicator(index, 'color', e.target.value)}"
          >
            <mwc-list-item value="red">Красный</mwc-list-item>
            <mwc-list-item value="green">Зеленый</mwc-list-item>
            <mwc-list-item value="yellow">Желтый</mwc-list-item>
          </ha-select>
        </div>
      </div>
    `).join('');
  }

  renderControlButtonsEditor() {
    const buttons = this._config.control_buttons || [];
    return buttons.map((button, index) => `
      <div class="item-editor">
        <div class="input-group">
          <label class="input-label">Метка: ${button.label || ''}</label>
        </div>
        <div class="input-group">
          <label class="input-label">Сенсор индикатора</label>
          <ha-entity-picker
            .hass="${this._hass}"
            .value="${button.indicator_entity || ''}"
            @value-changed="${(e) => this.updateControlButton(index, 'indicator_entity', e.detail.value)}"
          ></ha-entity-picker>
        </div>
        <div class="input-group">
          <label class="input-label">Цвет индикатора</label>
          <ha-select
            .value="${button.indicator_color || 'yellow'}"
            @selected="${(e) => this.updateControlButton(index, 'indicator_color', e.target.value)}"
          >
            <mwc-list-item value="red">Красный</mwc-list-item>
            <mwc-list-item value="green">Зеленый</mwc-list-item>
            <mwc-list-item value="yellow">Желтый</mwc-list-item>
          </ha-select>
        </div>
        <div class="input-group">
          <label class="input-label">Действие (tap_action JSON)</label>
          <ha-textfield
            .value="${button.tap_action ? JSON.stringify(button.tap_action) : ''}"
            @input="${(e) => this.updateControlButton(index, 'tap_action', e.target.value)}"
          ></ha-textfield>
        </div>
      </div>
    `).join('');
  }

  _valueChanged(key, value) {
    if (!this._config) return;
    this._config = { ...this._config, [key]: value };
    this.dispatchConfigChanged();
  }

  updateStatusIndicator(index, key, value) {
    const indicators = [...(this._config.status_indicators || [])];
    indicators[index] = { ...indicators[index], [key]: value };
    this._config = { ...this._config, status_indicators: indicators };
    this.dispatchConfigChanged();
  }

  updateDisplayValue(index, key, value) {
    const values = [...(this._config.display_values || [])];
    values[index] = { ...values[index], [key]: value };
    this._config = { ...this._config, display_values: values };
    this.dispatchConfigChanged();
  }

  updateSideIndicator(index, key, value) {
    const indicators = [...(this._config.side_indicators || [])];
    indicators[index] = { ...indicators[index], [key]: value };
    this._config = { ...this._config, side_indicators: indicators };
    this.dispatchConfigChanged();
  }

  updateControlButton(index, key, value) {
    const buttons = [...(this._config.control_buttons || [])];
    if (key === 'tap_action') {
      try {
        buttons[index] = { ...buttons[index], [key]: JSON.parse(value) };
      } catch (e) {
        return;
      }
    } else {
      buttons[index] = { ...buttons[index], [key]: value };
    }
    this._config = { ...this._config, control_buttons: buttons };
    this.dispatchConfigChanged();
  }

  addStatusIndicator() {
    const indicators = [...(this._config.status_indicators || [])];
    indicators.push({ label: '', entity: '', color: 'red' });
    this._config = { ...this._config, status_indicators: indicators };
    this.dispatchConfigChanged();
    this.render();
  }

  addDisplayValue() {
    const values = [...(this._config.display_values || [])];
    values.push({ label: '', entity: '' });
    this._config = { ...this._config, display_values: values };
    this.dispatchConfigChanged();
    this.render();
  }

  addSideIndicator() {
    const indicators = [...(this._config.side_indicators || [])];
    indicators.push({ label: '', entity: '', color: 'green' });
    this._config = { ...this._config, side_indicators: indicators };
    this.dispatchConfigChanged();
    this.render();
  }

  dispatchConfigChanged() {
    const event = new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

customElements.define('datakom-controller-card-editor', DatakomControllerCardEditor);
