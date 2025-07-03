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
            
            // Phone number examples by country code
            this.phoneExamples = {
                '966': '51 234 5678',  // Saudi Arabia
                '962': '7 9012 3456',  // Jordan
                '971': '50 123 4567',  // UAE
                '965': '9123 4567',    // Kuwait
                '973': '3612 3456',    // Bahrain
                '974': '5512 3456',    // Qatar
                '968': '9123 4567',    // Oman
                '1': '555 123 4567',   // USA/Canada
                '44': '7700 900123',   // UK
                '33': '6 12 34 56 78', // France
                '49': '30 12345678',   // Germany
                '39': '320 123 4567',  // Italy
                '34': '612 34 56 78',  // Spain
                '31': '6 12345678',    // Netherlands
                '32': '470 12 34 56',  // Belgium
                '41': '78 123 45 67',  // Switzerland
                '43': '664 123456',    // Austria
                '46': '70 123 45 67',  // Sweden
                '47': '412 34 567',    // Norway
                '45': '12 34 56 78',   // Denmark
                '358': '50 123 4567',  // Finland
                '91': '98765 43210',   // India
                '86': '138 0013 8000', // China
                '81': '90 1234 5678',  // Japan
                '82': '10 1234 5678',  // South Korea
                '60': '12 345 6789',   // Malaysia
                '65': '8123 4567',     // Singapore
                '852': '5123 4567',    // Hong Kong
                '61': '412 345 678',   // Australia
                '64': '21 123 4567',   // New Zealand
                '27': '82 123 4567',   // South Africa
                '20': '100 123 4567',  // Egypt
                '90': '532 123 45 67', // Turkey
                '98': '912 123 4567',  // Iran
                '92': '300 1234567',   // Pakistan
                '880': '171 2345678',  // Bangladesh
                '94': '71 234 5678',   // Sri Lanka
                '95': '9 123 456 789', // Myanmar
                '63': '917 123 4567',  // Philippines
                '66': '81 234 5678',   // Thailand
                '84': '91 234 56 78',  // Vietnam
                '62': '812 3456 789',  // Indonesia
                '7': '912 345 67 89',  // Russia/Kazakhstan
                '380': '67 123 4567',  // Ukraine
                '48': '512 345 678',   // Poland
                '420': '601 123 456',  // Czech Republic
                '421': '905 123 456',  // Slovakia
                '36': '20 123 4567',   // Hungary
                '40': '721 123 456',   // Romania
                '359': '87 123 4567',  // Bulgaria
                '385': '91 123 4567',  // Croatia
                '381': '60 1234567',   // Serbia
                '386': '31 123 456',   // Slovenia
                '387': '61 123 456',   // Bosnia and Herzegovina
                '389': '70 123 456',   // North Macedonia
                '382': '67 123 456',   // Montenegro
                '383': '44 123 456',   // Kosovo
                '355': '67 212 3456',  // Albania
                '30': '694 123 4567',  // Greece
                '357': '99 123456',    // Cyprus
                '356': '7921 2345',    // Malta
                '212': '6 12 34 56 78', // Morocco
                '213': '550 12 34 56', // Algeria
                '216': '20 123 456',   // Tunisia
                '218': '91 234 5678',  // Libya
                '249': '91 123 4567',  // Sudan
                '251': '91 123 4567',  // Ethiopia
                '254': '712 345678',   // Kenya
                '256': '712 345678',   // Uganda
                '255': '621 234 567',  // Tanzania
                '250': '788 123 456',  // Rwanda
                '257': '79 12 34 56',  // Burundi
                '260': '97 1234567',   // Zambia
                '263': '71 234 5678',  // Zimbabwe
                '265': '888 12 34 56', // Malawi
                '267': '71 123 456',   // Botswana
                '268': '7612 3456',    // Eswatini
                '266': '5012 3456',    // Lesotho
                '264': '81 123 4567'   // Namibia
            };

            if (this.countrySelect && this.phoneInput) {
                this.init();
            }
        }

        init() {
            // Set default country (Saudi Arabia)
            this.setDefaultCountry();
            
            // Bind events
            this.countrySelect.addEventListener('change', this.handleCountryChange.bind(this));
            this.phoneInput.addEventListener('input', this.handlePhoneInput.bind(this));
            
            // Make country selector searchable
            this.makeSelectSearchable();
            
            // Initial phone preview update and placeholder
            this.updatePhonePreview();
            this.updatePhonePlaceholder();
        }

        setDefaultCountry() {
            // Set Saudi Arabia as default
            const saudiOption = Array.from(this.countrySelect.options).find(option => 
                option.textContent.includes('Saudi Arabia') || option.getAttribute('data-code') === '966'
            );
            
            if (saudiOption) {
                saudiOption.selected = true;
                
                // Auto-populate phone field with default country code
                const countryCode = saudiOption.getAttribute('data-code');
                if (countryCode && !this.phoneInput.value.trim()) {
                    this.phoneInput.value = `+${countryCode} `;
                }
                
                this.updatePhonePreview();
                this.updatePhonePlaceholder();
            }
        }

        handleCountryChange(event) {
            // Auto-populate phone field with country code
            const selectedOption = this.countrySelect.selectedOptions[0];
            const countryCode = selectedOption ? selectedOption.getAttribute('data-code') : '';
            
            if (countryCode) {
                // Check if phone field is empty or only contains a country code
                const currentPhone = this.phoneInput.value.trim();
                const countryCodePrefix = `+${countryCode} `;
                
                // If phone field is empty, add country code
                if (!currentPhone) {
                    this.phoneInput.value = countryCodePrefix;
                } else {
                    // If phone field has content, check if it starts with a different country code
                    if (currentPhone.startsWith('+')) {
                        // Replace existing country code with new one
                        const phoneWithoutCode = currentPhone.replace(/^\+\d{1,4}\s*/, '');
                        this.phoneInput.value = countryCodePrefix + phoneWithoutCode;
                    } else {
                        // Add country code to existing number
                        this.phoneInput.value = countryCodePrefix + currentPhone;
                    }
                }
                
                // Focus cursor at the end of the phone field
                this.phoneInput.focus();
                this.phoneInput.setSelectionRange(this.phoneInput.value.length, this.phoneInput.value.length);
            }
            
            this.updatePhonePreview();
            this.updatePhonePlaceholder();
            
            // Re-validate phone number when country changes
            if (this.phoneInput.value) {
                this.validatePhoneNumber();
                
                // Also trigger main validation system if it exists
                const signupValidator = window.signupValidator;
                if (signupValidator && typeof signupValidator.validatePhone === 'function') {
                    signupValidator.validatePhone(this.phoneInput.value);
                }
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
            const countryCode = selectedOption ? selectedOption.getAttribute('data-phone-code') : '';
            const phoneNumber = this.phoneInput.value.trim();
            
            if (countryCode) {
                // If phone number already starts with +, use it as-is, otherwise add country code
                if (phoneNumber.startsWith('+')) {
                    this.phonePreview.textContent = phoneNumber;
                } else {
                    const fullNumber = phoneNumber ? `+${countryCode} ${phoneNumber}` : `+${countryCode} `;
                    this.phonePreview.textContent = fullNumber;
                }
            } else {
                this.phonePreview.textContent = phoneNumber;
            }
        }

        updatePhonePlaceholder() {
            const selectedOption = this.countrySelect.selectedOptions[0];
            const countryCode = selectedOption ? selectedOption.getAttribute('data-code') : '';
            
            if (countryCode && this.phoneExamples[countryCode]) {
                const exampleNumber = this.phoneExamples[countryCode];
                this.phoneInput.setAttribute('placeholder', exampleNumber);
            } else {
                // Default placeholder if no specific example found
                this.phoneInput.setAttribute('placeholder', 'Enter your phone number');
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
                    this.setPhoneValidationStatus('valid', 'Phone is valid');
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