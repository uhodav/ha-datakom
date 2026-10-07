class DatakomControllerCard extends HTMLElement {
  static _resourceCheckDone = false;
  static _resourceWarningShown = false;

  static checkResourceLoaded() {
    if (this._resourceCheckDone) return;
    this._resourceCheckDone = true;
    // Проверяем, зарегистрирован ли кастомный элемент
    if (!window.customCards || !window.customCards.some(card => card.type === 'datakom-controller-card')) {
      if (!this._resourceWarningShown) {
        this._resourceWarningShown = true;
        // Показываем предупреждение в UI
        const warning = document.createElement('div');
        warning.style.cssText = 'background:#e74c3c;color:#fff;padding:16px;border-radius:8px;font-size:16px;text-align:center;margin:16px 0;z-index:9999;';
        warning.innerHTML = '⚠️ Datakom Controller Card не загружена!<br>Карточка подключается интеграцией Datakom listener: обновите интеграцию и перезапустите Home Assistant.';
        // Вставляем предупреждение в начало body
        document.body.prepend(warning);
        // Также лог в консоль
        console.warn('Datakom Controller Card не загружена! Карточка подключается интеграцией Datakom listener: обновите интеграцию и перезапустите Home Assistant.');
      }
    }
  }
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    DatakomControllerCard.checkResourceLoaded();
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateStates();
  }

  getCardSize() {
    return 6;
  }

  render() {
    if (!this.config) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        
        .card-container {
          background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%);
          border: 3px solid #444;
          border-radius: 16px;
          padding: 20px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          font-family: 'Roboto', sans-serif;
          container-type: inline-size;
        }
        
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
        }
        
        .logo {
          color: #fff;
          font-size: 28px;
          font-weight: bold;
          letter-spacing: 2px;
        }
        
        .logo-icon {
          color: #e74c3c;
          margin-right: 8px;
        }
        
        .model {
          color: #999;
          font-size: 20px;
          font-weight: 300;
        }
        
        .main-layout {
          display: grid;
          grid-template-columns: minmax(74px, auto) 1fr minmax(74px, auto);
          gap: 10px;
          margin-bottom: 20px;
        }
        
        .status-section {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .status-title {
          color: #fff;
          font-size: 12px;
          font-weight: bold;
          text-transform: uppercase;
          letter-spacing: 1px;
          text-align: center;
        }
        
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 6px 10px;
          background: rgba(255,255,255,0.05);
          border-radius: 4px;
        }
        
        .status-label {
          color: #ccc;
          font-size: 10px;
          text-transform: uppercase;
          flex: 1;
        }
        
        .led {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #333;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
          transition: all 0.3s ease;
        }
        
        .led.on {
          box-shadow: 0 0 12px currentColor, inset 0 0 6px currentColor;
        }
        
        .led.green { color: #27ae60; }
        .led.red { color: #e74c3c; }
        .led.yellow { color: #f39c12; }
        
        .led.green.on { background: #27ae60; }
        .led.red.on { background: #e74c3c; }
        .led.yellow.on { background: #f39c12; }
        
        .display-section {
          background: #e8e8e8;
          border: 4px solid #555;
          border-radius: 8px;
          padding: 10px;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        
        .display-title {
          color: #2c3e50;
          font-size: 14px;
          font-weight: bold;
          text-align: center;
          margin-bottom: 12px;
          text-transform: uppercase;
        }
        
        .display-content {
          display: grid;
          gap: 3px;
        }
        
        .display-value {
          text-align: center;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 4px;
        }
        
        .display-label {
          color: #34495e;
          font-size: 11px;
          font-weight: 600;
          margin-bottom: 4px;
        }
        
        .display-number {
          color: #2c3e50;
          font-size: 24px;
          font-weight: bold;
          font-family: 'Courier New', monospace;
        }
        
        .side-indicators {
          display: flex;
          flex-direction: column;
          gap: 8px;
          justify-content: flex-start;
          padding-top: 20px;
        }
        
        .side-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 10px;
          background: rgba(255,255,255,0.05);
          border-radius: 4px;
        }
        
        .side-label {
          color: #ccc;
          font-size: 10px;
          text-transform: uppercase;
          flex: 1;
        }
        
        .side-led {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #333;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
          transition: all 0.3s ease;
        }
        
        .side-led.on {
          box-shadow: 0 0 12px currentColor, inset 0 0 6px currentColor;
        }
        
        .side-led.green { color: #27ae60; }
        .side-led.red { color: #e74c3c; }
        .side-led.yellow { color: #f39c12; }
        
        .side-led.green.on { background: #27ae60; }
        .side-led.red.on { background: #e74c3c; }
        .side-led.yellow.on { background: #f39c12; }
        .side-led.fail {
          background: #e74c3c;
          box-shadow: 0 0 12px #e74c3c, inset 0 0 6px #e74c3c;
        }

        .led.blink, .side-led.blink, .button-indicator.blink {
          animation: led-blink 0.8s steps(1) infinite;
        }

        @keyframes led-blink {
          50% { opacity: 0.15; }
        }

        .mimic {
          display: grid;
          grid-template-columns: 14px 26px auto;
          grid-template-rows: auto 34px auto 34px auto;
          align-items: center;
          column-gap: 6px;
          color: #ccc;
          font-size: 10px;
          text-transform: uppercase;
        }

        .mimic ha-icon {
          --mdc-icon-size: 22px;
          color: #ddd;
        }

        .mimic-label {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .mimic-line {
          justify-self: center;
          width: 2px;
          height: 100%;
          background: #666;
        }

        .mimic-switch {
          position: relative;
          justify-self: center;
          width: 26px;
          height: 34px;
        }

        .mimic-switch::before, .mimic-switch::after {
          content: '';
          position: absolute;
          left: 12px;
          width: 2px;
          height: 8px;
          background: #666;
        }

        .mimic-switch::before { top: 0; }
        .mimic-switch::after { bottom: 0; }

        .mimic-blade {
          position: absolute;
          left: 12px;
          top: 8px;
          width: 2px;
          height: 18px;
          background: #888;
          transform-origin: bottom center;
          transform: rotate(35deg);
          transition: transform 0.3s ease, background 0.3s ease;
        }

        .mimic-switch.closed .mimic-blade {
          transform: rotate(0deg);
          background: #27ae60;
        }
        
        .control-buttons {
          display: flex;
          justify-content: space-around;
          gap: 12px;
        }
        
        .control-button {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          flex: 1;
        }
        
        .button-circle {
          width: 70px;
          height: 70px;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
          background-position: center !important;
          background-repeat: no-repeat !important;
          background-size: cover !important;
          border-radius: 50%;
        }
        
        .button-circle:hover {
          transform: scale(1.05);
          box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        }
        
        .button-circle:active {
          transform: scale(0.98);
        }
        
        .button-indicator {
          position: absolute;
          top: 3px;
          right: 1px;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: #333;
          border: 2px solid #2c2c2c;
          transition: all 0.3s ease;
          text-align: center;
          font-size: 40px;
          line-height: 1.75;
        }
        
        .button-indicator.on {
          box-shadow: 0 0 12px currentColor;
        }
        .button-indicator.green.on {
          background: #27ae60;
          border-color: #4ec37f;
        }
        .button-indicator.red.on {
          background: #e74c3c;
          border-color: #a36059;
        }
        .button-indicator.yellow.on {
          background: #f39c12;
          border-color: #d4a300;
        }
        
        .button-label {
          color: #fff;
          font-size: 13px;
          font-weight: bold;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        
        .btn-test { background: #f1c40f; border-color: #d4a300; color: #000; }
        .btn-auto { background: #2c2c2c; border-color: #666; color: #fff; }
        .btn-manual { background: #2c2c2c; border-color: #666; color: #fff; }
        .btn-stop { background: #e74c3c; border-color: #c0392b; color: #fff; }
        .btn-run { background: #27ae60; border-color: #229954; color: #fff; }
        
        /* Responsive styles */
        @container (max-width: 400px) {
          .button-circle {
            width: 50px;
            height: 50px;
            font-size: 24px;
          }
          
          .button-label {
            font-size: 11px;
          }
          
          .button-indicator {
            width: 12px;
            height: 12px;
            top: 2px;
            right: 0px;
          }
        }
        
        @container (max-width: 300px) {
          .control-button.hide-if-small {
            display: none;
          }
        }
        
        .error-message {
          color: #e74c3c;
          text-align: center;
          padding: 20px;
        }
      </style>
      
      <div class="card-container">
        <div class="header">
          <div class="logo">
            <span class="logo-icon">●</span>DATAKOM
          </div>
          <div class="model">${this.config.model || 'D 500'}</div>
        </div>
        
        <div class="main-layout">
          <!-- Left: Status Indicators -->
          <div class="status-section">
            <div class="status-title">${this.config.status_title || ''}</div>
            ${this.renderStatusIndicators()}
          </div>
          
          <!-- Center: Display -->
          <div class="display-section">
            <div class="display-title">${this.config.display_title || ''}</div>
            <div class="display-content" id="display-content">
              ${this.renderDisplayContent()}
            </div>
          </div>
          
          <!-- Right: Mimic Diagram -->
          <div class="side-indicators">
            ${this.renderMimic()}
          </div>
        </div>
        
        <!-- Control Buttons -->
        <div class="control-buttons">
          ${this.renderControlButtons()}
        </div>
      </div>
    `;
    
    this.setupEventListeners();
  }

  renderStatusIndicators() {
    const indicators = this.config.status_indicators || [];
    return indicators.map(indicator => `
      <div class="status-indicator">
        <span class="status-label">${indicator.label || ''}</span>
        <div class="led ${indicator.color || 'red'}" data-entity="${[].concat(indicator.entity || []).join(',')}"></div>
      </div>
    `).join('');
  }

  renderDisplayContent() {
    const displayValues = this.config.display_values || [];
    return displayValues.map(item => `
      <div class="display-value">
        <div class="display-label">${item.label || ''}</div>
        <div class="display-number" data-entity="${item.entity || ''}">--</div>
      </div>
    `).join('');
  }

  renderSideIndicators() {
    const indicators = this.config.side_indicators || [];
    return indicators.map(indicator => `
      <div class="side-indicator">
        <span class="side-label">${indicator.label || ''}</span>
        <div class="side-led ${indicator.color || 'green'}" data-entity="${indicator.entity || ''}"></div>
      </div>
    `).join('');
  }

  renderMimic() {
    const m = this.getMimicEntities();
    return `
      <div class="mimic">
        <div class="side-led green" data-entity="${m.mains}" data-fail-entity="${m.mains_fail}"></div>
        <ha-icon icon="mdi:transmission-tower"></ha-icon>
        <span class="mimic-label">MAINS</span>
        <div class="side-led green" data-entity="${m.mcb}"></div>
        <div class="mimic-switch" data-entity="${m.mcb}"><div class="mimic-blade"></div></div>
        <span></span>
        <span></span>
        <div class="mimic-line"></div>
        <span class="mimic-label"><ha-icon icon="mdi:factory"></ha-icon>LOAD</span>
        <div class="side-led yellow" data-entity="${m.gcb}"></div>
        <div class="mimic-switch" data-entity="${m.gcb}"><div class="mimic-blade"></div></div>
        <span></span>
        <div class="side-led yellow" data-entity="${m.genset}"></div>
        <ha-icon icon="mdi:engine"></ha-icon>
        <span class="mimic-label">GENSET</span>
      </div>
    `;
  }

  getMimicEntities() {
    // Совместимость со старой конфигурацией side_indicators (MAINS / GENSET)
    const legacy = {};
    (this.config.side_indicators || []).forEach(i => { legacy[(i.label || '').toLowerCase()] = i.entity; });
    const mimic = this.config.mimic || {};
    return {
      mains: mimic.mains || legacy.mains || 'binary_sensor.datakom_device_mains',
      mains_fail: mimic.mains_fail || 'binary_sensor.datakom_device_mains_fail',
      mcb: mimic.mcb || 'binary_sensor.datakom_device_mcb',
      gcb: mimic.gcb || 'binary_sensor.datakom_device_gcb',
      genset: mimic.genset || legacy.genset || 'binary_sensor.datakom_device_genset',
    };
  }

  renderControlButtons() {
    const buttons = this.config.control_buttons || [
      { action: 'test', label: 'TEST', class: 'btn-test', icon: '⚙', indicator_entity: 'binary_sensor.test', indicator_color: 'yellow' },
      { action: 'auto', label: 'AUTO', class: 'btn-auto', icon: '🔧', indicator_entity: 'binary_sensor.auto', indicator_color: 'green' },
      { action: 'manual', label: 'MAN', class: 'btn-manual', icon: '✋', indicator_entity: 'binary_sensor.manual', indicator_color: 'yellow' },
      { action: 'stop', label: 'STOP', class: 'btn-stop', icon: 'O', indicator_entity: 'binary_sensor.stop', indicator_color: 'yellow' },
      { action: 'run', label: 'RUN', class: 'btn-run', icon: 'I', indicator_entity: 'binary_sensor.run', indicator_color: 'yellow' }
    ];
    
    return buttons.map(btn => {
      let iconContent = btn.icon || '';
      let buttonStyle = '';
      
      // Если указаны картинки, используем их
      if (btn.image_on || btn.image_off) {
        iconContent = '';
        buttonStyle = `data-image-on="${btn.image_on || ''}" data-image-off="${btn.image_off || ''}"`;
      }
      
      // Добавляем класс для скрытия на малых экранах
      const hideClass = btn.hide_if_small ? 'hide-if-small' : '';
      
      // Добавляем атрибут button_entity для вызова кнопки Home Assistant
      const buttonEntityAttr = btn.button_entity ? `data-button-entity="${btn.button_entity}"` : '';
      
      return `
        <div class="control-button ${hideClass}">
          <div class="button-circle ${btn.class || ''}" 
               data-action="${btn.action || ''}" 
               data-tap-action="${btn.tap_action || ''}"
               ${buttonEntityAttr}
               ${buttonStyle}>
            ${iconContent}
            <div class="button-indicator ${btn.indicator_color || 'yellow'}" data-entity="${btn.indicator_entity || ''}"></div>
          </div>
          <div class="button-label">${btn.label || ''}</div>
        </div>
      `;
    }).join('');
  }

  setupEventListeners() {
    // Control button clicks
    this.shadowRoot.querySelectorAll('.button-circle').forEach(button => {
      button.addEventListener('click', (e) => {
        const action = e.currentTarget.getAttribute('data-action');
        const tapAction = e.currentTarget.getAttribute('data-tap-action');
        const buttonEntity = e.currentTarget.getAttribute('data-button-entity');
        
        // Если указан button_entity, вызываем сервис кнопки
        if (buttonEntity && this._hass) {
          this._hass.callService('button', 'press', {
            entity_id: buttonEntity
          });
          
          // Через 3 секунды обновляем состояния
          setTimeout(() => {
            this.updateStates();
          }, 3000);
        } 
        // Иначе используем старый способ с tap_action
        else if (tapAction) {
          this.handleTapAction(JSON.parse(tapAction));
        }
      });
    });
  }

  handleTapAction(tapAction) {
    if (!tapAction || !this._hass) return;
    
    switch (tapAction.action) {
      case 'call-service':
        this._hass.callService(
          tapAction.service.split('.')[0],
          tapAction.service.split('.')[1],
          tapAction.service_data || {}
        );
        break;
      case 'navigate':
        window.location.hash = tapAction.navigation_path;
        break;
      case 'more-info':
        const event = new Event('hass-more-info', {
          bubbles: true,
          composed: true,
        });
        event.detail = { entityId: tapAction.entity };
        this.dispatchEvent(event);
        break;
    }
  }

  // Состояние LED по одной или нескольким сущностям (через запятую): горит если горит любая
  ledState(entityAttr) {
    const result = { known: false, on: false, blink: false };
    (entityAttr || '').split(',').filter(Boolean).forEach(entity => {
      const stateObj = this._hass.states[entity];
      if (!stateObj) return;
      result.known = true;
      if (stateObj.state === 'on' || stateObj.state === 'true') {
        result.on = true;
        result.blink = result.blink || stateObj.attributes.blink === true;
      }
    });
    return result;
  }

  updateStates() {
    if (!this._hass || !this.shadowRoot) return;

    // Update status, side and mimic LEDs
    this.shadowRoot.querySelectorAll('.status-indicator .led, .side-led').forEach(led => {
      const state = this.ledState(led.getAttribute('data-entity'));
      if (state.known) {
        led.classList.toggle('on', state.on);
        led.classList.toggle('blink', state.blink);
      }
      // MAINS - двухцветный LED: красный при аварии сети
      const failEntity = led.getAttribute('data-fail-entity');
      if (failEntity) {
        led.classList.toggle('fail', !state.on && this.ledState(failEntity).on);
      }
    });

    // Update mimic contactors
    this.shadowRoot.querySelectorAll('.mimic-switch').forEach(sw => {
      const state = this.ledState(sw.getAttribute('data-entity'));
      sw.classList.toggle('closed', state.on && !state.blink);
    });
    
    // Update button indicators и картинки
    this.shadowRoot.querySelectorAll('.button-circle').forEach(button => {
      const indicator = button.querySelector('.button-indicator');
      if (indicator) {
        const ledState = this.ledState(indicator.getAttribute('data-entity'));
        if (ledState.known) {
          const isOn = ledState.on;
          indicator.classList.toggle('on', isOn);
          indicator.classList.toggle('blink', ledState.blink);
          
          // Обновляем картинки кнопок если они указаны
          const imageOn = button.getAttribute('data-image-on');
          const imageOff = button.getAttribute('data-image-off');
          
          if (imageOn && imageOff) {
            button.style.backgroundImage = `url('${isOn ? imageOn : imageOff}')`;
          }
        }
      }
    });
    
    // Update display values
    this.shadowRoot.querySelectorAll('.display-number').forEach(display => {
      const entity = display.getAttribute('data-entity');
      if (entity && this._hass.states[entity]) {
        const state = this._hass.states[entity];
        const value = parseFloat(state.state);
        display.textContent = isNaN(value) ? state.state : Math.round(value);
      }
    });
  }

  static getConfigElement() {
    return document.createElement('datakom-controller-card-editor');
  }

  static getStubConfig() {
    return {
      model: 'D 500',
      display_title: 'State',
      status_indicators: [
        { label: 'AUTO READY', color: 'green', entity: 'binary_sensor.datakom_device_auto_ready' },
        { label: 'ALARM', color: 'red', entity: ['binary_sensor.datakom_device_alarm_shutdown', 'binary_sensor.datakom_device_alarm_loaddump'] },
        { label: 'WARNING', color: 'red', entity: 'binary_sensor.datakom_device_alarm_warning' },
        { label: 'SERVICE REQUEST', color: 'red', entity: '' },
        { label: 'LED 1', color: 'red', entity: 'binary_sensor.datakom_device_prog1' },
        { label: 'LED 2', color: 'red', entity: 'binary_sensor.datakom_device_prog2' }
      ],
      display_values: [
        { label: 'Fuel', entity: 'sensor.engine_fuel_level' },
        { label: 'kWt', entity: 'sensor.genset_tot_active_pwr' },
        { label: 'L3', entity: 'sensor.genset_l3' }
      ],
      mimic: {
        mains: 'binary_sensor.datakom_device_mains',
        mains_fail: 'binary_sensor.datakom_device_mains_fail',
        mcb: 'binary_sensor.datakom_device_mcb',
        gcb: 'binary_sensor.datakom_device_gcb',
        genset: 'binary_sensor.datakom_device_genset'
      },
      control_buttons: [
        { 
          action: 'test', 
          label: 'TEST', 
          class: 'btn-test', 
          icon: '⚙',
          image_on: '/ha_datakom/img/test-k.png',
          image_off: '/ha_datakom/img/test.png',
          indicator_entity: 'binary_sensor.test', 
          indicator_color: 'yellow',
          button_entity: 'button.datakom_device_control_test'
        },
        { 
          action: 'auto', 
          label: 'AUTO', 
          class: 'btn-auto', 
          icon: '🔧',
          image_on: '/ha_datakom/img/auto-k.png',
          image_off: '/ha_datakom/img/auto.png',
          indicator_entity: 'binary_sensor.auto', 
          indicator_color: 'green',
          button_entity: 'button.datakom_device_control_auto'
        },
        { 
          action: 'manual', 
          label: 'MAN', 
          class: 'btn-manual', 
          icon: '✋',
          image_on: '/ha_datakom/img/manual-k.png',
          image_off: '/ha_datakom/img/manual.png',
          indicator_entity: 'binary_sensor.manual', 
          indicator_color: 'yellow',
          button_entity: 'button.datakom_device_control_manual'
        },
        { 
          action: 'stop', 
          label: 'STOP', 
          class: 'btn-stop', 
          icon: 'O',
          image_on: '/ha_datakom/img/stop-k.png',
          image_off: '/ha_datakom/img/stop.png',
          indicator_entity: 'binary_sensor.stop', 
          indicator_color: 'yellow',
          button_entity: 'button.datakom_device_control_stop'
        },
        { 
          action: 'run', 
          label: 'RUN', 
          class: 'btn-run', 
          icon: 'I',
          image_on: '/ha_datakom/img/run-k.png',
          image_off: '/ha_datakom/img/run.png',
          indicator_entity: 'binary_sensor.run', 
          indicator_color: 'yellow'
        }
      ]
    };
  }
}

if (!customElements.get('datakom-controller-card')) {
  customElements.define('datakom-controller-card', DatakomControllerCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === 'datakom-controller-card')) window.customCards.push({
  type: 'datakom-controller-card',
  name: 'Datakom Controller Card',
  description: 'Custom card for Datakom generator controller interface',
  preview: true,
  documentationURL: 'https://github.com/uhodav/ha-datakom'
});

// Горизонтальная мнемосхема: MAINS — MCB — LOAD — GCB — GENSET
class DatakomMimicCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    this.config = {
      mains: 'binary_sensor.datakom_device_mains',
      mains_fail: 'binary_sensor.datakom_device_mains_fail',
      mcb: 'binary_sensor.datakom_device_mcb',
      gcb: 'binary_sensor.datakom_device_gcb',
      genset: 'binary_sensor.datakom_device_genset',
      mains_color: '#27ae60',
      mains_fail_color: '#e74c3c',
      genset_color: '#f1c40f',
      style: 'modern',
      image_path: '/ha_datakom/img/',
      ...(config || {}),
    };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateStates();
  }

  getCardSize() {
    return 3;
  }

  static getStubConfig() {
    return {
      mains: 'binary_sensor.datakom_device_mains',
      mcb: 'binary_sensor.datakom_device_mcb',
      gcb: 'binary_sensor.datakom_device_gcb',
      genset: 'binary_sensor.datakom_device_genset',
    };
  }

  renderSwitch(id, label) {
    return `
      <div class="switch" id="${id}">
        <span class="switch-label">${label}</span>
        <svg viewBox="0 0 60 24" preserveAspectRatio="none">
          <line class="wire" x1="0" y1="16" x2="14" y2="16"></line>
          <circle class="contact" cx="16" cy="16" r="3"></circle>
          <line class="blade" x1="16" y1="16" x2="44" y2="16"></line>
          <circle class="contact" cx="44" cy="16" r="3"></circle>
          <line class="wire" x1="46" y1="16" x2="60" y2="16"></line>
        </svg>
      </div>
    `;
  }

  // Вид как на портале Datakom: картинки контакторов и кнопок MAINS / GENSET с LED (канва 352x70)
  renderClassic() {
    const img = this.config.image_path;
    const pct = (v, total) => `${(v / total) * 100}%`;
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .title { font-size: 16px; font-weight: 500; margin-bottom: 8px; color: var(--primary-text-color); }
        .classic {
          position: relative;
          width: 100%;
          max-width: 528px;
          aspect-ratio: 352 / 70;
          margin: 0 auto;
          background: #fff;
          border-radius: 8px;
        }
        .classic img { position: absolute; top: 0; }
        .classic .led {
          position: absolute;
          width: ${pct(10, 352)};
          aspect-ratio: 1;
          border-radius: 50%;
          background: #C0C0C0;
        }
      </style>
      <ha-card>
        ${this.config.title ? `<div class="title">${this.config.title}</div>` : ''}
        <div class="classic">
          <img src="${img}BTN_MainsLedOff.png" style="left: 0; width: ${pct(48, 352)};">
          <div class="led" id="mains-led" style="left: ${pct(35, 352)}; top: ${pct(3, 70)};"></div>
          <img id="mimic-img" src="${img}MainsOff_GenOff.png" style="left: ${pct(112, 352)}; width: ${pct(128, 352)};">
          <img src="${img}BTN_GenLedOff.png" style="left: ${pct(304, 352)}; width: ${pct(48, 352)};">
          <div class="led" id="genset-led" style="left: ${pct(339, 352)}; top: ${pct(3, 70)};"></div>
        </div>
      </ha-card>
    `;
    this.updateStates();
  }

  // Цвет LED как на портале: значение 1 - жёлтый, 2 - зелёный (атрибут led_value)
  classicLedColor(entity, fallback) {
    const stateObj = entity && this._hass && this._hass.states[entity];
    if (!stateObj || stateObj.state !== 'on') return '#C0C0C0';
    const value = stateObj.attributes.led_value;
    if (value === 1) return '#FFF500';
    if (value === 2) return '#54C247';
    return fallback;
  }

  render() {
    if (!this.config) return;
    if (this.config.style === 'classic') {
      this.renderClassic();
      return;
    }
    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
          --wire-off: #888;
          --wire-on: #4caf50;
        }
        .title {
          font-size: 16px;
          font-weight: 500;
          margin-bottom: 8px;
          color: var(--primary-text-color);
        }
        .mimic {
          display: flex;
          align-items: center;
        }
        .node {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          flex: 0 0 auto;
        }
        .led {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #666;
          transition: all 0.3s ease;
        }
        .led.placeholder {
          visibility: hidden;
        }
        .circle {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          border: 2px solid var(--wire-off);
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--card-background-color, #1c1c1c);
          transition: border-color 0.3s ease;
        }
        .circle ha-icon {
          --mdc-icon-size: 32px;
          color: var(--primary-text-color);
        }
        .load .circle {
          width: 78px;
          height: 78px;
          border-width: 3px;
        }
        .node.on .circle {
          border-color: var(--wire-on);
        }
        .node-label {
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--primary-text-color);
        }
        .wire-seg {
          flex: 1 1 0;
          min-width: 8px;
          height: 4px;
          background: var(--wire-off);
          border-radius: 2px;
          margin-top: 18px;
          transition: background 0.3s ease;
        }
        .wire-seg.on {
          background: var(--wire-on);
        }
        .switch {
          flex: 1.2 1 0;
          min-width: 40px;
          display: flex;
          flex-direction: column;
          align-items: center;
          margin-top: 18px;
        }
        .switch svg {
          width: 100%;
          height: 24px;
          overflow: visible;
        }
        .switch-label {
          font-size: 11px;
          font-weight: 600;
          color: var(--secondary-text-color);
          margin-bottom: -6px;
        }
        .switch line {
          stroke: var(--wire-off);
          stroke-width: 4;
          stroke-linecap: round;
          transition: stroke 0.3s ease;
        }
        .switch circle {
          fill: var(--wire-off);
          transition: fill 0.3s ease;
        }
        .switch .blade {
          transform-origin: 16px 16px;
          transform: rotate(-25deg);
          transition: transform 0.3s ease, stroke 0.3s ease;
        }
        .switch.closed .blade {
          transform: rotate(0deg);
        }
        .switch.on line, .switch.on .blade {
          stroke: var(--wire-on);
        }
        .switch.on circle {
          fill: var(--wire-on);
        }
      </style>
      <ha-card>
        ${this.config.title ? `<div class="title">${this.config.title}</div>` : ''}
        <div class="mimic">
          <div class="node" id="mains-node">
            <div class="led" id="mains-led"></div>
            <div class="circle"><ha-icon icon="mdi:transmission-tower"></ha-icon></div>
            <span class="node-label">MAINS</span>
          </div>
          <div class="wire-seg" id="mains-wire"></div>
          ${this.renderSwitch('mcb', 'MCB')}
          <div class="wire-seg" id="mains-load-wire"></div>
          <div class="node load" id="load-node">
            <div class="led placeholder"></div>
            <div class="circle"><ha-icon icon="mdi:factory"></ha-icon></div>
            <span class="node-label">LOAD</span>
          </div>
          <div class="wire-seg" id="genset-load-wire"></div>
          ${this.renderSwitch('gcb', 'GCB')}
          <div class="wire-seg" id="genset-wire"></div>
          <div class="node" id="genset-node">
            <div class="led" id="genset-led"></div>
            <div class="circle"><ha-icon icon="mdi:engine"></ha-icon></div>
            <span class="node-label">GENSET</span>
          </div>
        </div>
      </ha-card>
    `;
    this.updateStates();
  }

  isOn(entity) {
    const stateObj = entity && this._hass && this._hass.states[entity];
    return !!stateObj && stateObj.state === 'on';
  }

  updateStates() {
    if (!this._hass) return;
    const root = this.shadowRoot;
    if (this.config.style === 'classic') {
      const mimicImg = root.getElementById('mimic-img');
      if (!mimicImg) return;
      const mcbOn = this.isOn(this.config.mcb);
      const gcbOn = this.isOn(this.config.gcb);
      mimicImg.src = `${this.config.image_path}Mains${mcbOn ? 'On' : 'Off'}_Gen${gcbOn ? 'On' : 'Off'}.png`;
      const mainsColor = this.classicLedColor(this.config.mains, '#54C247');
      root.getElementById('mains-led').style.background =
        mainsColor === '#C0C0C0' && this.isOn(this.config.mains_fail) ? this.config.mains_fail_color : mainsColor;
      root.getElementById('genset-led').style.background = this.classicLedColor(this.config.genset, '#FFF500');
      return;
    }
    if (!root.querySelector('.mimic')) return;
    const mains = this.isOn(this.config.mains);
    const mcb = this.isOn(this.config.mcb);
    const gcb = this.isOn(this.config.gcb);
    const genset = this.isOn(this.config.genset);
    const fromMains = mains && mcb;
    const fromGenset = genset && gcb;

    const setLed = (id, on, color) => {
      const led = root.getElementById(id);
      led.style.background = on ? color : '';
      led.style.boxShadow = on ? `0 0 10px ${color}` : '';
    };
    if (!mains && this.isOn(this.config.mains_fail)) {
      setLed('mains-led', true, this.config.mains_fail_color);
    } else {
      setLed('mains-led', mains, this.config.mains_color);
    }
    setLed('genset-led', genset, this.config.genset_color);

    root.getElementById('mains-node').classList.toggle('on', mains);
    root.getElementById('genset-node').classList.toggle('on', genset);
    root.getElementById('load-node').classList.toggle('on', fromMains || fromGenset);
    root.getElementById('mains-wire').classList.toggle('on', mains);
    root.getElementById('genset-wire').classList.toggle('on', genset);
    root.getElementById('mains-load-wire').classList.toggle('on', fromMains);
    root.getElementById('genset-load-wire').classList.toggle('on', fromGenset);

    const mcbEl = root.getElementById('mcb');
    mcbEl.classList.toggle('closed', mcb);
    mcbEl.classList.toggle('on', fromMains);
    const gcbEl = root.getElementById('gcb');
    gcbEl.classList.toggle('closed', gcb);
    gcbEl.classList.toggle('on', fromGenset);
  }
}

if (!customElements.get('datakom-mimic-card')) {
  customElements.define('datakom-mimic-card', DatakomMimicCard);
}

if (!window.customCards.some(card => card.type === 'datakom-mimic-card')) window.customCards.push({
  type: 'datakom-mimic-card',
  name: 'Datakom Mimic Card',
  description: 'Mains / genset mimic diagram (MCB, GCB, load)',
  preview: true,
  documentationURL: 'https://github.com/uhodav/ha-datakom'
});

console.info(
  '%c DATAKOM-CONTROLLER-CARD %c v1.5.0 ',
  'color: white; background: #e74c3c; font-weight: 700;',
  'color: #e74c3c; background: white; font-weight: 700;'
);
