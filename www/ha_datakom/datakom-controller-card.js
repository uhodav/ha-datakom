class DatakomControllerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
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
          
          <!-- Right: Side Indicators -->
          <div class="side-indicators">
            ${this.renderSideIndicators()}
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
        <div class="led ${indicator.color || 'red'}" data-entity="${indicator.entity || ''}"></div>
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

  renderControlButtons() {
    const buttons = this.config.control_buttons || [
      { action: 'test', label: 'TEST', class: 'btn-test', icon: '⚙', indicator_entity: 'binary_sensor.test', indicator_color: 'yellow' },
      { action: 'auto', label: 'AUTO', class: 'btn-auto', icon: '🔧', indicator_entity: 'binary_sensor.auto', indicator_color: 'green' },
      { action: 'manual', label: 'MAN', class: 'btn-manual', icon: '✋', indicator_entity: 'binary_sensor.manual', indicator_color: 'yellow' },
      { action: 'stop', label: 'STOP', class: 'btn-stop', icon: 'O', indicator_entity: 'binary_sensor.stop', indicator_color: 'red' },
      { action: 'run', label: 'RUN', class: 'btn-run', icon: 'I', indicator_entity: 'binary_sensor.run', indicator_color: 'green' }
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

  updateStates() {
    if (!this._hass || !this.shadowRoot) return;
    
    // Update status LEDs
    this.shadowRoot.querySelectorAll('.status-indicator .led').forEach(led => {
      const entity = led.getAttribute('data-entity');
      if (entity && this._hass.states[entity]) {
        const state = this._hass.states[entity].state;
        led.classList.toggle('on', state === 'on' || state === 'true');
      }
    });
    
    // Update side LEDs (используем ту же логику что и для status indicators)
    this.shadowRoot.querySelectorAll('.side-indicator .side-led').forEach(led => {
      const entity = led.getAttribute('data-entity');
      if (entity && this._hass.states[entity]) {
        const state = this._hass.states[entity].state;
        led.classList.toggle('on', state === 'on' || state === 'true');
      }
    });
    
    // Update button indicators и картинки
    this.shadowRoot.querySelectorAll('.button-circle').forEach(button => {
      const indicator = button.querySelector('.button-indicator');
      if (indicator) {
        const entity = indicator.getAttribute('data-entity');
        if (entity && this._hass.states[entity]) {
          const state = this._hass.states[entity].state;
          const isOn = state === 'on' || state === 'true';
          indicator.classList.toggle('on', isOn);
          
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
        { label: 'AUTO READY', color: 'green', entity: 'binary_sensor.auto' },
        { label: 'ALARM', color: 'red', entity: 'binary_sensor.alarm_shutdown' },
        { label: 'WARNING', color: 'red', entity: 'binary_sensor.alarm_warning' }
      ],
      display_values: [
        { label: 'Fuel', entity: 'sensor.engine_fuel_level' },
        { label: 'kWt', entity: 'sensor.genset_tot_active_pwr' },
        { label: 'L3', entity: 'sensor.genset_l3' }
      ],
      side_indicators: [
        { label: 'MAINS', color: 'green', entity: 'binary_sensor.mains' },
        { label: 'GENSET', color: 'green', entity: 'binary_sensor.genset' }
      ],
      control_buttons: [
        { 
          action: 'test', 
          label: 'TEST', 
          class: 'btn-test', 
          icon: '⚙',
          image_on: '/local/community/datakom/img/test_on.png',
          image_off: '/local/community/datakom/img/test_off.png',
          indicator_entity: 'binary_sensor.test', 
          indicator_color: 'yellow',
          button_entity: 'button.datakom_device_control_test'
        },
        { 
          action: 'auto', 
          label: 'AUTO', 
          class: 'btn-auto', 
          icon: '🔧',
          image_on: '/local/community/datakom/img/auto_on.png',
          image_off: '/local/community/datakom/img/auto_off.png',
          indicator_entity: 'binary_sensor.auto', 
          indicator_color: 'green',
          button_entity: 'button.datakom_device_control_auto'
        },
        { 
          action: 'manual', 
          label: 'MAN', 
          class: 'btn-manual', 
          icon: '✋',
          image_on: '/local/community/datakom/img/manual_on.png',
          image_off: '/local/community/datakom/img/manual_off.png',
          indicator_entity: 'binary_sensor.manual', 
          indicator_color: 'yellow',
          button_entity: 'button.datakom_device_control_manual'
        },
        { 
          action: 'stop', 
          label: 'STOP', 
          class: 'btn-stop', 
          icon: 'O',
          image_on: '/local/community/datakom/img/stop_on.png',
          image_off: '/local/community/datakom/img/stop_off.png',
          indicator_entity: 'binary_sensor.stop', 
          indicator_color: 'red',
          button_entity: 'button.datakom_device_control_stop'
        },
        { 
          action: 'run', 
          label: 'RUN', 
          class: 'btn-run', 
          icon: 'I',
          image_on: '/local/community/datakom/img/run_on.png',
          image_off: '/local/community/datakom/img/run_off.png',
          indicator_entity: 'binary_sensor.run', 
          indicator_color: 'green',
          button_entity: 'button.datakom_device_control_run'
        }
      ]
    };
  }
}

customElements.define('datakom-controller-card', DatakomControllerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'datakom-controller-card',
  name: 'Datakom Controller Card',
  description: 'Custom card for Datakom generator controller interface',
  preview: true,
  documentationURL: 'https://github.com/uhodav/ha-datakom'
});

console.info(
  '%c DATAKOM-CONTROLLER-CARD %c v1.0.0 ',
  'color: white; background: #e74c3c; font-weight: 700;',
  'color: #e74c3c; background: white; font-weight: 700;'
);
