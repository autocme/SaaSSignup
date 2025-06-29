/**
 * Country Phone Selector Module
 * Handles country selection and phone number formatting
 */

(function() {
    'use strict';

    class CountryPhoneSelector {
        constructor() {
            this.countrySelect = document.getElementById('phone_country');
            this.phoneInput = document.getElementById('phone');
            this.phonePreview = document.getElementById('phone-preview-text');
            
            // Country code to flag emoji mapping
            this.countryFlags = {
                'AD': '🇦🇩', 'AE': '🇦🇪', 'AF': '🇦🇫', 'AG': '🇦🇬', 'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲',
                'AO': '🇦🇴', 'AQ': '🇦🇶', 'AR': '🇦🇷', 'AS': '🇦🇸', 'AT': '🇦🇹', 'AU': '🇦🇺', 'AW': '🇦🇼',
                'AX': '🇦🇽', 'AZ': '🇦🇿', 'BA': '🇧🇦', 'BB': '🇧🇧', 'BD': '🇧🇩', 'BE': '🇧🇪', 'BF': '🇧🇫',
                'BG': '🇧🇬', 'BH': '🇧🇭', 'BI': '🇧🇮', 'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BN': '🇧🇳',
                'BO': '🇧🇴', 'BQ': '🇧🇶', 'BR': '🇧🇷', 'BS': '🇧🇸', 'BT': '🇧🇹', 'BV': '🇧🇻', 'BW': '🇧🇼',
                'BY': '🇧🇾', 'BZ': '🇧🇿', 'CA': '🇨🇦', 'CC': '🇨🇨', 'CD': '🇨🇩', 'CF': '🇨🇫', 'CG': '🇨🇬',
                'CH': '🇨🇭', 'CI': '🇨🇮', 'CK': '🇨🇰', 'CL': '🇨🇱', 'CM': '🇨🇲', 'CN': '🇨🇳', 'CO': '🇨🇴',
                'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'CZ': '🇨🇿',
                'DE': '🇩🇪', 'DJ': '🇩🇯', 'DK': '🇩🇰', 'DM': '🇩🇲', 'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨',
                'EE': '🇪🇪', 'EG': '🇪🇬', 'EH': '🇪🇭', 'ER': '🇪🇷', 'ES': '🇪🇸', 'ET': '🇪🇹', 'FI': '🇫🇮',
                'FJ': '🇫🇯', 'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'FR': '🇫🇷', 'GA': '🇬🇦', 'GB': '🇬🇧',
                'GD': '🇬🇩', 'GE': '🇬🇪', 'GF': '🇬🇫', 'GG': '🇬🇬', 'GH': '🇬🇭', 'GI': '🇬🇮', 'GL': '🇬🇱',
                'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵', 'GQ': '🇬🇶', 'GR': '🇬🇷', 'GS': '🇬🇸', 'GT': '🇬🇹',
                'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HK': '🇭🇰', 'HM': '🇭🇲', 'HN': '🇭🇳', 'HR': '🇭🇷',
                'HT': '🇭🇹', 'HU': '🇭🇺', 'ID': '🇮🇩', 'IE': '🇮🇪', 'IL': '🇮🇱', 'IM': '🇮🇲', 'IN': '🇮🇳',
                'IO': '🇮🇴', 'IQ': '🇮🇶', 'IR': '🇮🇷', 'IS': '🇮🇸', 'IT': '🇮🇹', 'JE': '🇯🇪', 'JM': '🇯🇲',
                'JO': '🇯🇴', 'JP': '🇯🇵', 'KE': '🇰🇪', 'KG': '🇰🇬', 'KH': '🇰🇭', 'KI': '🇰🇮', 'KM': '🇰🇲',
                'KN': '🇰🇳', 'KP': '🇰🇵', 'KR': '🇰🇷', 'KW': '🇰🇼', 'KY': '🇰🇾', 'KZ': '🇰🇿', 'LA': '🇱🇦',
                'LB': '🇱🇧', 'LC': '🇱🇨', 'LI': '🇱🇮', 'LK': '🇱🇰', 'LR': '🇱🇷', 'LS': '🇱🇸', 'LT': '🇱🇹',
                'LU': '🇱🇺', 'LV': '🇱🇻', 'LY': '🇱🇾', 'MA': '🇲🇦', 'MC': '🇲🇨', 'MD': '🇲🇩', 'ME': '🇲🇪',
                'MF': '🇲🇫', 'MG': '🇲🇬', 'MH': '🇲🇭', 'MK': '🇲🇰', 'ML': '🇲🇱', 'MM': '🇲🇲', 'MN': '🇲🇳',
                'MO': '🇲🇴', 'MP': '🇲🇵', 'MQ': '🇲🇶', 'MR': '🇲🇷', 'MS': '🇲🇸', 'MT': '🇲🇹', 'MU': '🇲🇺',
                'MV': '🇲🇻', 'MW': '🇲🇼', 'MX': '🇲🇽', 'MY': '🇲🇾', 'MZ': '🇲🇿', 'NA': '🇳🇦', 'NC': '🇳🇨',
                'NE': '🇳🇪', 'NF': '🇳🇫', 'NG': '🇳🇬', 'NI': '🇳🇮', 'NL': '🇳🇱', 'NO': '🇳🇴', 'NP': '🇳🇵',
                'NR': '🇳🇷', 'NU': '🇳🇺', 'NZ': '🇳🇿', 'OM': '🇴🇲', 'PA': '🇵🇦', 'PE': '🇵🇪', 'PF': '🇵🇫',
                'PG': '🇵🇬', 'PH': '🇵🇭', 'PK': '🇵🇰', 'PL': '🇵🇱', 'PM': '🇵🇲', 'PN': '🇵🇳', 'PR': '🇵🇷',
                'PS': '🇵🇸', 'PT': '🇵🇹', 'PW': '🇵🇼', 'PY': '🇵🇾', 'QA': '🇶🇦', 'RE': '🇷🇪', 'RO': '🇷🇴',
                'RS': '🇷🇸', 'RU': '🇷🇺', 'RW': '🇷🇼', 'SA': '🇸🇦', 'SB': '🇸🇧', 'SC': '🇸🇨', 'SD': '🇸🇩',
                'SE': '🇸🇪', 'SG': '🇸🇬', 'SH': '🇸🇭', 'SI': '🇸🇮', 'SJ': '🇸🇯', 'SK': '🇸🇰', 'SL': '🇸🇱',
                'SM': '🇸🇲', 'SN': '🇸🇳', 'SO': '🇸🇴', 'SR': '🇸🇷', 'SS': '🇸🇸', 'ST': '🇸🇹', 'SV': '🇸🇻',
                'SX': '🇸🇽', 'SY': '🇸🇾', 'SZ': '🇸🇿', 'TC': '🇹🇨', 'TD': '🇹🇩', 'TF': '🇹🇫', 'TG': '🇹🇬',
                'TH': '🇹🇭', 'TJ': '🇹🇯', 'TK': '🇹🇰', 'TL': '🇹🇱', 'TM': '🇹🇲', 'TN': '🇹🇳', 'TO': '🇹🇴',
                'TR': '🇹🇷', 'TT': '🇹🇹', 'TV': '🇹🇻', 'TW': '🇹🇼', 'TZ': '🇹🇿', 'UA': '🇺🇦', 'UG': '🇺🇬',
                'UM': '🇺🇲', 'US': '🇺🇸', 'UY': '🇺🇾', 'UZ': '🇺🇿', 'VA': '🇻🇦', 'VC': '🇻🇨', 'VE': '🇻🇪',
                'VG': '🇻🇬', 'VI': '🇻🇮', 'VN': '🇻🇳', 'VU': '🇻🇺', 'WF': '🇼🇫', 'WS': '🇼🇸', 'YE': '🇾🇪',
                'YT': '🇾🇹', 'ZA': '🇿🇦', 'ZM': '🇿🇲', 'ZW': '🇿🇼'
            };
            
            if (this.countrySelect && this.phoneInput) {
                this.init();
            }
        }

        init() {
            // Add flags to country options
            this.addFlagsToCountryOptions();
            
            // Set default country (Saudi Arabia)
            this.setDefaultCountry();
            
            // Bind events
            this.countrySelect.addEventListener('change', this.handleCountryChange.bind(this));
            this.phoneInput.addEventListener('input', this.handlePhoneInput.bind(this));
            
            // Make country selector searchable
            this.makeSelectSearchable();
            
            // Initial phone preview update
            this.updatePhonePreview();
        }
        
        addFlagsToCountryOptions() {
            // Create custom dropdown with flag images
            this.createCustomCountryDropdown();
        }
        
        createCustomCountryDropdown() {
            // Hide the original select
            this.countrySelect.style.display = 'none';
            
            // Create custom dropdown container
            const customDropdown = document.createElement('div');
            customDropdown.className = 'custom-country-dropdown';
            customDropdown.innerHTML = `
                <div class="country-selected" id="country-selected">
                    <span class="country-flag"></span>
                    <span class="country-text">Select Country</span>
                    <i class="fa fa-chevron-down dropdown-arrow"></i>
                </div>
                <div class="country-options" id="country-options" style="display: none;">
                    <!-- Options will be populated by JavaScript -->
                </div>
            `;
            
            // Insert after the original select
            this.countrySelect.parentNode.insertBefore(customDropdown, this.countrySelect.nextSibling);
            
            // Populate options
            this.populateCustomOptions();
            
            // Bind events
            this.bindCustomDropdownEvents();
        }
        
        populateCustomOptions() {
            const optionsContainer = document.getElementById('country-options');
            
            Array.from(this.countrySelect.options).forEach(option => {
                if (option.value) {
                    const flagUrl = option.getAttribute('data-flag-url');
                    const countryCode = option.getAttribute('data-country-code');
                    const phoneCode = option.getAttribute('data-code');
                    const countryName = option.textContent.split(' +')[0]; // Remove phone code from name
                    
                    const optionDiv = document.createElement('div');
                    optionDiv.className = 'country-option';
                    optionDiv.setAttribute('data-value', option.value);
                    optionDiv.setAttribute('data-code', phoneCode);
                    optionDiv.setAttribute('data-country-code', countryCode);
                    
                    // Use flag image if available, otherwise use emoji fallback
                    let flagDisplay = '';
                    if (flagUrl && flagUrl !== 'False') {
                        flagDisplay = `<img class="country-flag-img" src="${flagUrl}" alt="${countryCode}"/>`;
                    } else {
                        const flag = this.countryFlags[countryCode] || '🏳️';
                        flagDisplay = `<span class="country-flag-emoji">${flag}</span>`;
                    }
                    
                    optionDiv.innerHTML = `
                        ${flagDisplay}
                        <span class="country-name">${countryName}</span>
                        <span class="country-phone-code">+${phoneCode}</span>
                    `;
                    
                    optionsContainer.appendChild(optionDiv);
                }
            });
        }
        
        bindCustomDropdownEvents() {
            const selectedDiv = document.getElementById('country-selected');
            const optionsDiv = document.getElementById('country-options');
            
            // Toggle dropdown
            selectedDiv.addEventListener('click', () => {
                const isVisible = optionsDiv.style.display === 'block';
                optionsDiv.style.display = isVisible ? 'none' : 'block';
                selectedDiv.classList.toggle('active', !isVisible);
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.custom-country-dropdown')) {
                    optionsDiv.style.display = 'none';
                    selectedDiv.classList.remove('active');
                }
            });
            
            // Handle option selection
            optionsDiv.addEventListener('click', (e) => {
                const option = e.target.closest('.country-option');
                if (option) {
                    const value = option.getAttribute('data-value');
                    const phoneCode = option.getAttribute('data-code');
                    const countryCode = option.getAttribute('data-country-code');
                    
                    // Update original select
                    this.countrySelect.value = value;
                    
                    // Update display
                    const flagElement = option.querySelector('.country-flag-img, .country-flag-emoji');
                    const nameElement = option.querySelector('.country-name');
                    
                    selectedDiv.querySelector('.country-flag').innerHTML = flagElement.outerHTML;
                    selectedDiv.querySelector('.country-text').textContent = `${nameElement.textContent} +${phoneCode}`;
                    
                    // Close dropdown
                    optionsDiv.style.display = 'none';
                    selectedDiv.classList.remove('active');
                    
                    // Trigger change event
                    this.countrySelect.dispatchEvent(new Event('change'));
                }
            });
        }

        setDefaultCountry() {
            // Set Saudi Arabia as default after custom dropdown is created
            setTimeout(() => {
                const selectedDiv = document.getElementById('country-selected');
                const saudiOption = document.querySelector('.country-option[data-country-code="SA"]');
                
                if (saudiOption && selectedDiv) {
                    // Trigger selection of Saudi Arabia
                    saudiOption.click();
                }
            }, 100);
        }

        handleCountryChange(event) {
            this.updatePhonePreview();
            
            // Clear and re-validate phone number when country changes
            if (this.phoneInput.value) {
                this.validatePhoneNumber();
            }
        }

        handlePhoneInput(event) {
            this.updatePhonePreview();
            
            // Add debounced validation
            clearTimeout(this.phoneValidationTimeout);
            this.phoneValidationTimeout = setTimeout(() => {
                this.validatePhoneNumber();
            }, 500);
        }

        updatePhonePreview() {
            const selectedOption = this.countrySelect.selectedOptions[0];
            const countryCode = selectedOption ? selectedOption.getAttribute('data-code') : '';
            const phoneNumber = this.phoneInput.value.trim();
            
            if (countryCode) {
                const fullNumber = phoneNumber ? `+${countryCode} ${phoneNumber}` : `+${countryCode} `;
                this.phonePreview.textContent = fullNumber;
            } else {
                this.phonePreview.textContent = phoneNumber;
            }
        }

        async validatePhoneNumber() {
            const phoneNumber = this.phoneInput.value.trim();
            const countryId = this.countrySelect.value;
            
            if (!phoneNumber || !countryId) return;

            try {
                // Show loading state
                this.setPhoneValidationStatus('loading', 'Validating...');
                
                const response = await this.makeAjaxRequest('/j_signup_validation/validate_phone', {
                    phone: phoneNumber,
                    country_id: countryId
                });

                if (response.valid) {
                    this.setPhoneValidationStatus('valid', 'Valid phone number');
                } else {
                    this.setPhoneValidationStatus('invalid', response.messages.join(', '));
                }
            } catch (error) {
                console.error('Phone validation error:', error);
                this.setPhoneValidationStatus('error', 'Validation failed');
            }
        }

        setPhoneValidationStatus(status, message) {
            const statusElement = document.querySelector('.phone-validation-status');
            if (!statusElement) return;

            // Remove existing classes
            this.phoneInput.classList.remove('is-valid', 'is-invalid', 'loading');
            statusElement.className = 'phone-validation-status';

            switch (status) {
                case 'valid':
                    this.phoneInput.classList.add('is-valid');
                    statusElement.classList.add('text-success');
                    statusElement.innerHTML = `<i class="fa fa-check"></i> ${message}`;
                    break;
                case 'invalid':
                    this.phoneInput.classList.add('is-invalid');
                    statusElement.classList.add('text-danger');
                    statusElement.innerHTML = `<i class="fa fa-times"></i> ${message}`;
                    break;
                case 'loading':
                    this.phoneInput.classList.add('loading');
                    statusElement.classList.add('text-muted');
                    statusElement.innerHTML = `<i class="fa fa-spinner fa-spin"></i> ${message}`;
                    break;
                case 'error':
                    statusElement.classList.add('text-warning');
                    statusElement.innerHTML = `<i class="fa fa-exclamation-triangle"></i> ${message}`;
                    break;
            }
        }

        makeSelectSearchable() {
            // Simple search functionality for the select
            let searchTimeout;
            let searchQuery = '';

            this.countrySelect.addEventListener('keydown', (event) => {
                if (event.key.length === 1) {
                    searchQuery += event.key.toLowerCase();
                    
                    // Find matching option
                    const options = Array.from(this.countrySelect.options);
                    const matchingOption = options.find(option => 
                        option.textContent.toLowerCase().includes(searchQuery) ||
                        option.getAttribute('data-code')?.includes(searchQuery)
                    );
                    
                    if (matchingOption) {
                        matchingOption.selected = true;
                        this.updatePhonePreview();
                    }
                    
                    // Clear search query after delay
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        searchQuery = '';
                    }, 1000);
                }
            });
        }

        async makeAjaxRequest(url, data) {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: data,
                    id: Date.now()
                })
            });

            const result = await response.json();
            if (result.error) {
                throw new Error(result.error.message);
            }
            
            return result.result;
        }
    }

    // Initialize when DOM is loaded
    function initCountryPhoneSelector() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                new CountryPhoneSelector();
            });
        } else {
            new CountryPhoneSelector();
        }
    }

    // Auto-initialize
    initCountryPhoneSelector();

})();