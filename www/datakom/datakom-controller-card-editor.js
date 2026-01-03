class DatakomControllerCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._debounceTimers = {};
  }

  setConfig(config) {
    this._config = { ...config };
    // Initialize arrays if not present
    if (!this._config.status_indicators) this._config.status_indicators = [];
    if (!this._config.display_values) this._config.display_values = [];
    if (!this._config.side_indicators) this._config.side_indicators = [];
    if (!this._config.control_buttons) this._config.control_buttons = [];
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    // Only render if config exists and hass wasn't set before
    if (this._config && !this._hassSet) {
      this._hassSet = true;
      this.render();
    }
  }

  configChanged(newConfig) {
    const event = new Event('config-changed', {
      bubbles: true,
      composed: true,
    });
    event.detail = { config: newConfig };
    this.dispatchEvent(event);
  }

  render() {
    if (!this._config) return;

    // Save scroll position before re-render
    const scrollContainer = this.shadowRoot.querySelector('.card-config');
    const scrollTop = scrollContainer ? scrollContainer.scrollTop : 0;

    this.shadowRoot.innerHTML = `
      <style>
        .card-config {
          padding: 16px;
        }
        
        .option {
          margin-bottom: 16px;
        }
        
        .option label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .option input, .option select {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          box-sizing: border-box;
        }
        
        .section-title {
          font-size: 16px;
          font-weight: bold;
          color: var(--primary-text-color);
          margin: 24px 0 12px 0;
          padding-bottom: 8px;
          border-bottom: 2px solid var(--divider-color);
        }
        
        .array-item {
          background: var(--secondary-background-color);
          padding: 12px;
          margin-bottom: 8px;
          border-radius: 4px;
          border: 1px solid var(--divider-color);
        }
        
        .array-item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .array-item-title {
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .btn {
          padding: 6px 12px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }
        
        .btn-add {
          background: var(--primary-color);
          color: white;
          margin-top: 8px;
        }
        
        .btn-add:hover {
          opacity: 0.8;
        }
        
        .btn-remove {
          background: var(--error-color);
          color: white;
          font-size: 12px;
          padding: 4px 8px;
        }
        
        .btn-remove:hover {
          opacity: 0.8;
        }
        
        .hint {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 4px;
        }
        
        .grid-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
      </style>
      
      <div class="card-config">
        <div class="section-title">Загальні налаштування / General Settings</div>
        
        <div class="option">
          <label>Model / Модель</label>
          <input 
            type="text" 
            id="model" 
            value="${this._config.model || 'D 500'}"
            placeholder="D-500 MK3"
          />
          <div class="hint">Назва моделі контролера / Controller model name</div>
        </div>
        
        <div class="option">
          <label>Display Title / Заголовок дисплею</label>
          <input 
            type="text" 
            id="display_title" 
            value="${this._config.display_title || 'GEN PHASE VOLTAGES'}"
            placeholder="State / Властивості"
          />
          <div class="hint">Текст над дисплеєм / Text above display section</div>
        </div>
        
        <div class="section-title">Status Indicators / Індикатори стану (ліва панель)</div>
        <div id="status-indicators-container"></div>
        <button class="btn btn-add" id="add-status-indicator">+ Add Status Indicator</button>
        
        <div class="section-title">Display Values / Значення дисплею (центр)</div>
        <div id="display-values-container"></div>
        <button class="btn btn-add" id="add-display-value">+ Add Display Value</button>
        
        <div class="section-title">Side Indicators / Бічні індикатори (права панель)</div>
        <div id="side-indicators-container"></div>
        <button class="btn btn-add" id="add-side-indicator">+ Add Side Indicator</button>
        
        <div class="section-title">Control Buttons / Кнопки керування</div>
        <div id="control-buttons-container"></div>
        <button class="btn btn-add" id="add-control-button">+ Add Control Button</button>
      </div>
    `;

    this.renderStatusIndicators();
    this.renderDisplayValues();
    this.renderSideIndicators();
    this.renderControlButtons();
    this.setupEntityPickers();
    this.attachEventListeners();
    
    // Restore scroll position after re-render
    requestAnimationFrame(() => {
      const newScrollContainer = this.shadowRoot.querySelector('.card-config');
      if (newScrollContainer && scrollTop > 0) {
        newScrollContainer.scrollTop = scrollTop;
      }
    });
  }

  setupEntityPickers() {
    // Set hass for all ha-entity-picker elements
    if (this._hass) {
      this.shadowRoot.querySelectorAll('ha-entity-picker').forEach(picker => {
        picker.hass = this._hass;
      });
    }
  }

  renderStatusIndicators() {
    const container = this.shadowRoot.getElementById('status-indicators-container');
    const indicators = this._config.status_indicators || [];
    
    container.innerHTML = indicators.map((indicator, index) => `
      <div class="array-item">
        <div class="array-item-header">
          <span class="array-item-title">Indicator ${index + 1}</span>
          <button class="btn btn-remove" data-type="status" data-index="${index}">Remove</button>
        </div>
        <div class="option">
          <label>Label</label>
          <input type="text" data-type="status" data-index="${index}" data-field="label" value="${indicator.label || ''}" />
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Color</label>
            <select data-type="status" data-index="${index}" data-field="color">
              <option value="green" ${indicator.color === 'green' ? 'selected' : ''}>Green</option>
              <option value="red" ${indicator.color === 'red' ? 'selected' : ''}>Red</option>
              <option value="yellow" ${indicator.color === 'yellow' ? 'selected' : ''}>Yellow</option>
            </select>
          </div>
          <div class="option">
            <label>Entity</label>
            <ha-entity-picker
              data-type="status"
              data-index="${index}"
              data-field="entity"
              .value="${indicator.entity || ''}"
              .includeDomains='["binary_sensor"]'
              allow-custom-entity
            ></ha-entity-picker>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderDisplayValues() {
    const container = this.shadowRoot.getElementById('display-values-container');
    const values = this._config.display_values || [];
    
    container.innerHTML = values.map((value, index) => `
      <div class="array-item">
        <div class="array-item-header">
          <span class="array-item-title">Display Value ${index + 1}</span>
          <button class="btn btn-remove" data-type="display" data-index="${index}">Remove</button>
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Label</label>
            <input type="text" data-type="display" data-index="${index}" data-field="label" value="${value.label || ''}" placeholder="Fuel" />
          </div>
          <div class="option">
            <label>Entity</label>
            <ha-entity-picker
              data-type="display"
              data-index="${index}"
              data-field="entity"
              .value="${value.entity || ''}"
              .includeDomains='["sensor"]'
              allow-custom-entity
            ></ha-entity-picker>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderSideIndicators() {
    const container = this.shadowRoot.getElementById('side-indicators-container');
    const indicators = this._config.side_indicators || [];
    
    container.innerHTML = indicators.map((indicator, index) => `
      <div class="array-item">
        <div class="array-item-header">
          <span class="array-item-title">Side Indicator ${index + 1}</span>
          <button class="btn btn-remove" data-type="side" data-index="${index}">Remove</button>
        </div>
        <div class="option">
          <label>Label</label>
          <input type="text" data-type="side" data-index="${index}" data-field="label" value="${indicator.label || ''}" />
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Color</label>
            <select data-type="side" data-index="${index}" data-field="color">
              <option value="green" ${indicator.color === 'green' ? 'selected' : ''}>Green</option>
              <option value="red" ${indicator.color === 'red' ? 'selected' : ''}>Red</option>
              <option value="yellow" ${indicator.color === 'yellow' ? 'selected' : ''}>Yellow</option>
            </select>
          </div>
          <div class="option">
            <label>Entity</label>
            <ha-entity-picker
              data-type="side"
              data-index="${index}"
              data-field="entity"
              .value="${indicator.entity || ''}"
              .includeDomains='["binary_sensor"]'
              allow-custom-entity
            ></ha-entity-picker>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderControlButtons() {
    const container = this.shadowRoot.getElementById('control-buttons-container');
    const buttons = this._config.control_buttons || [];
    
    container.innerHTML = buttons.map((button, index) => `
      <div class="array-item">
        <div class="array-item-header">
          <span class="array-item-title">Button ${index + 1}: ${button.label || ''}</span>
          <button class="btn btn-remove" data-type="button" data-index="${index}">Remove</button>
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Label</label>
            <input type="text" data-type="button" data-index="${index}" data-field="label" value="${button.label || ''}" placeholder="AUTO" />
          </div>
          <div class="option">
            <label>Action</label>
            <input type="text" data-type="button" data-index="${index}" data-field="action" value="${button.action || ''}" placeholder="auto" />
          </div>
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Class</label>
            <input type="text" data-type="button" data-index="${index}" data-field="class" value="${button.class || ''}" placeholder="btn-auto" />
          </div>
          <div class="option">
            <label>Icon</label>
            <input type="text" data-type="button" data-index="${index}" data-field="icon" value="${button.icon || ''}" placeholder="🔧" />
          </div>
        </div>
        <div class="option">
          <label>Image ON (active state)</label>
          <input type="text" data-type="button" data-index="${index}" data-field="image_on" value="${button.image_on || ''}" placeholder="/local/community/datakom/img/auto-k.png" />
        </div>
        <div class="option">
          <label>Image OFF (inactive state)</label>
          <input type="text" data-type="button" data-index="${index}" data-field="image_off" value="${button.image_off || ''}" placeholder="/local/community/datakom/img/auto.png" />
        </div>
        <div class="grid-2">
          <div class="option">
            <label>Indicator Entity</label>
            <ha-entity-picker
              data-type="button"
              data-index="${index}"
              data-field="indicator_entity"
              .value="${button.indicator_entity || ''}"
              .includeDomains='["binary_sensor"]'
              allow-custom-entity
            ></ha-entity-picker>
          </div>
          <div class="option">
            <label>Indicator Color</label>
            <select data-type="button" data-index="${index}" data-field="indicator_color">
              <option value="green" ${button.indicator_color === 'green' ? 'selected' : ''}>Green</option>
              <option value="red" ${button.indicator_color === 'red' ? 'selected' : ''}>Red</option>
              <option value="yellow" ${button.indicator_color === 'yellow' ? 'selected' : ''}>Yellow</option>
            </select>
          </div>
        </div>
        <div class="option">
          <label>Button Entity (для управления)</label>
          <ha-entity-picker
            data-type="button"
            data-index="${index}"
            data-field="button_entity"
            .value="${button.button_entity || ''}"
            .includeDomains='["button"]'
            allow-custom-entity
          ></ha-entity-picker>
        </div>
        <div class="option" style="display: flex; gap: 8px;">
          <div>
            <input type="checkbox" data-type="button" data-index="${index}" data-field="hide_if_small" ${button.hide_if_small ? 'checked' : ''} />
          </div>
          <span>Hide on small</span>
        </div>
      </div>
    `).join('');
  }

  attachEventListeners() {
    // Model and display title
    const modelInput = this.shadowRoot.getElementById('model');
    if (modelInput) {
      modelInput.addEventListener('input', (e) => {
        this._config.model = e.target.value;
        clearTimeout(this._debounceTimers['model']);
        this._debounceTimers['model'] = setTimeout(() => {
          this.configChanged(this._config);
        }, 500);
      });
      modelInput.addEventListener('blur', () => {
        clearTimeout(this._debounceTimers['model']);
        this.configChanged(this._config);
      });
    }

    const displayTitleInput = this.shadowRoot.getElementById('display_title');
    if (displayTitleInput) {
      displayTitleInput.addEventListener('input', (e) => {
        this._config.display_title = e.target.value;
        clearTimeout(this._debounceTimers['display_title']);
        this._debounceTimers['display_title'] = setTimeout(() => {
          this.configChanged(this._config);
        }, 500);
      });
      displayTitleInput.addEventListener('blur', () => {
        clearTimeout(this._debounceTimers['display_title']);
        this.configChanged(this._config);
      });
    }

    // Add buttons
    this.shadowRoot.getElementById('add-status-indicator')?.addEventListener('click', () => {
      if (!this._config.status_indicators) this._config.status_indicators = [];
      this._config.status_indicators.push({ label: 'New Indicator', color: 'green', entity: '' });
      this.configChanged(this._config);
      this.render();
    });

    this.shadowRoot.getElementById('add-display-value')?.addEventListener('click', () => {
      if (!this._config.display_values) this._config.display_values = [];
      this._config.display_values.push({ label: 'Value', entity: '' });
      this.configChanged(this._config);
      this.render();
    });

    this.shadowRoot.getElementById('add-side-indicator')?.addEventListener('click', () => {
      if (!this._config.side_indicators) this._config.side_indicators = [];
      this._config.side_indicators.push({ label: 'Indicator', color: 'green', entity: '' });
      this.configChanged(this._config);
      this.render();
    });

    this.shadowRoot.getElementById('add-control-button')?.addEventListener('click', () => {
      if (!this._config.control_buttons) this._config.control_buttons = [];
      this._config.control_buttons.push({
        action: 'action',
        label: 'BUTTON',
        class: 'btn-auto',
        icon: '⚙',
        indicator_entity: '',
        indicator_color: 'yellow'
      });
      this.configChanged(this._config);
      this.render();
    });

    // Array item inputs
    this.shadowRoot.querySelectorAll('input[data-type], select[data-type]').forEach(input => {
      const eventType = input.type === 'checkbox' ? 'change' : 'input';
      input.addEventListener(eventType, (e) => {
        const type = e.target.dataset.type;
        const index = parseInt(e.target.dataset.index);
        const field = e.target.dataset.field;
        const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;

        let array;
        switch (type) {
          case 'status':
            array = this._config.status_indicators;
            break;
          case 'display':
            array = this._config.display_values;
            break;
          case 'side':
            array = this._config.side_indicators;
            break;
          case 'button':
            array = this._config.control_buttons;
            break;
        }

        if (array && array[index]) {
          array[index][field] = value;
          
          // Update item title if label field changed, without full re-render
          if (field === 'label' && type === 'button') {
            const itemHeader = e.target.closest('.array-item')?.querySelector('.array-item-title');
            if (itemHeader) {
              itemHeader.textContent = `Button ${index + 1}: ${value}`;
            }
          }
          
          // For text inputs, use debounce to avoid frequent config changes
          if (e.target.type === 'text') {
            const timerId = `${type}-${index}-${field}`;
            clearTimeout(this._debounceTimers[timerId]);
            this._debounceTimers[timerId] = setTimeout(() => {
              this.configChanged(this._config);
            }, 500);
          } else {
            // For selects and checkboxes, fire immediately
            this.configChanged(this._config);
          }
        }
      });
      
      // Also fire on blur for text inputs to save immediately when leaving the field
      if (input.type === 'text') {
        input.addEventListener('blur', (e) => {
          const type = e.target.dataset.type;
          const index = e.target.dataset.index;
          const field = e.target.dataset.field;
          const timerId = `${type}-${index}-${field}`;
          clearTimeout(this._debounceTimers[timerId]);
          this.configChanged(this._config);
        });
      }
    });

    // Entity picker value-changed events
    this.shadowRoot.querySelectorAll('ha-entity-picker').forEach(picker => {
      picker.addEventListener('value-changed', (e) => {
        const type = e.target.dataset.type;
        const index = parseInt(e.target.dataset.index);
        const field = e.target.dataset.field;
        const value = e.detail.value;

        let array;
        switch (type) {
          case 'status':
            array = this._config.status_indicators;
            break;
          case 'display':
            array = this._config.display_values;
            break;
          case 'side':
            array = this._config.side_indicators;
            break;
          case 'button':
            array = this._config.control_buttons;
            break;
        }

        if (array && array[index]) {
          array[index][field] = value;
          this.configChanged(this._config);
        }
      });
    });

    // Remove buttons
    this.shadowRoot.querySelectorAll('.btn-remove').forEach(button => {
      button.addEventListener('click', (e) => {
        const type = e.target.dataset.type;
        const index = parseInt(e.target.dataset.index);

        switch (type) {
          case 'status':
            this._config.status_indicators.splice(index, 1);
            break;
          case 'display':
            this._config.display_values.splice(index, 1);
            break;
          case 'side':
            this._config.side_indicators.splice(index, 1);
            break;
          case 'button':
            this._config.control_buttons.splice(index, 1);
            break;
        }

        this.configChanged(this._config);
        this.render();
      });
    });
  }
}

customElements.define('datakom-controller-card-editor', DatakomControllerCardEditor);
