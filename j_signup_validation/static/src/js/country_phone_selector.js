/**
 * Country Phone Selector Module
 * Handles country selection and phone number formatting
 */

console.log('CountryPhoneSelector: Script file loaded');

(function() {
    'use strict';
    
    console.log('CountryPhoneSelector: IIFE started');

    class CountryPhoneSelector {
        constructor() {
            console.log('CountryPhoneSelector: Constructor called');
            
            this.countrySelect = document.getElementById('phone_country');
            this.phoneInput = document.getElementById('phone');
            this.phonePreview = document.getElementById('phone-preview-text');
            
            console.log('CountryPhoneSelector: Elements found:', {
                countrySelect: !!this.countrySelect,
                phoneInput: !!this.phoneInput,
                phonePreview: !!this.phonePreview
            });

            if (this.countrySelect && this.phoneInput) {
                console.log('CountryPhoneSelector: Initializing...');
                this.init();
            } else {
                console.log('CountryPhoneSelector: Required elements not found, skipping initialization');
            }
        }

        init() {
            // Set default country (Saudi Arabia)
            this.setDefaultCountry();
            
            // Bind events
            this.countrySelect.addEventListener('change', this.handleCountryChange.bind(this));
            this.phoneInput.addEventListener('input', this.handlePhoneInput.bind(this));
            
            // Add focus event to ensure country code is added when user focuses on phone field
            this.phoneInput.addEventListener('focus', this.handlePhoneFocus.bind(this));
            
            // Make country selector searchable
            this.makeSelectSearchable();
            
            // Initial phone preview update
            this.updatePhonePreview();
        }
        
        handlePhoneFocus(event) {
            // If phone field is empty when focused, add country code
            if (!this.phoneInput.value.trim()) {
                const selectedOption = this.countrySelect.options[this.countrySelect.selectedIndex];
                if (selectedOption && selectedOption.getAttribute('data-code')) {
                    const countryCode = selectedOption.getAttribute('data-code');
                    this.phoneInput.value = `+${countryCode} `;
                    console.log('CountryPhoneSelector: Added country code on focus:', this.phoneInput.value);
                }
            }
        }

        setDefaultCountry() {
            console.log('CountryPhoneSelector: Setting default country');
            
            // Use setTimeout to ensure DOM is ready
            setTimeout(() => {
                // Set Saudi Arabia as default
                const saudiOption = Array.from(this.countrySelect.options).find(option => 
                    option.textContent.includes('Saudi Arabia') || option.getAttribute('data-code') === '966'
                );
                
                console.log('CountryPhoneSelector: Saudi option found:', saudiOption);
                
                if (saudiOption) {
                    saudiOption.selected = true;
                    console.log('CountryPhoneSelector: Saudi Arabia selected, updating phone field');
                    
                    // Auto-populate phone field with country code
                    this.updatePhoneFieldWithCountryCode();
                    this.updatePhonePreview();
                } else {
                    console.log('CountryPhoneSelector: Saudi Arabia option not found');
                }
            }, 100);
        }

        handleCountryChange(event) {
            this.updatePhoneFieldWithCountryCode();
            this.updatePhonePreview();
            
            // Clear and re-validate phone number when country changes
            if (this.phoneInput.value) {
                this.validatePhoneNumber();
            }
        }
        
        updatePhoneFieldWithCountryCode() {
            if (!this.countrySelect || !this.phoneInput) {
                console.log('CountryPhoneSelector: Elements not found');
                return;
            }
            
            const selectedOption = this.countrySelect.options[this.countrySelect.selectedIndex];
            console.log('CountryPhoneSelector: Selected option:', selectedOption);
            
            if (selectedOption && selectedOption.getAttribute('data-code')) {
                const countryCode = selectedOption.getAttribute('data-code');
                const currentPhone = this.phoneInput.value || '';
                
                console.log('CountryPhoneSelector: Country code:', countryCode, 'Current phone:', currentPhone);
                
                // Remove any existing country code from the phone input
                let phoneWithoutCode = currentPhone;
                if (currentPhone.startsWith('+')) {
                    // Remove existing country code (1-4 digits after +)
                    phoneWithoutCode = currentPhone.replace(/^\+\d{1,4}\s*/, '');
                }
                
                // Add the new country code to the phone input
                const newPhoneValue = `+${countryCode} ${phoneWithoutCode}`.trim();
                console.log('CountryPhoneSelector: Setting phone to:', newPhoneValue);
                
                this.phoneInput.value = newPhoneValue;
                
                // Trigger input event to update validation and preview
                this.phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
                this.phoneInput.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                console.log('CountryPhoneSelector: No selected option or data-code found');
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
    
    console.log('CountryPhoneSelector: IIFE completed');

})();

// Fallback initialization outside IIFE
console.log('CountryPhoneSelector: Fallback initialization attempt');
setTimeout(() => {
    const countrySelect = document.getElementById('phone_country');
    const phoneInput = document.getElementById('phone');
    
    console.log('CountryPhoneSelector: Fallback - Elements check:', {
        countrySelect: !!countrySelect,
        phoneInput: !!phoneInput
    });
    
    if (countrySelect && phoneInput && !countrySelect.hasAttribute('data-initialized')) {
        console.log('CountryPhoneSelector: Fallback - Manual initialization');
        countrySelect.setAttribute('data-initialized', 'true');
        
        // Manual country code addition
        countrySelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption && selectedOption.getAttribute('data-code')) {
                const countryCode = selectedOption.getAttribute('data-code');
                const currentPhone = phoneInput.value || '';
                let phoneWithoutCode = currentPhone;
                
                if (currentPhone.startsWith('+')) {
                    phoneWithoutCode = currentPhone.replace(/^\+\d{1,4}\s*/, '');
                }
                
                phoneInput.value = `+${countryCode} ${phoneWithoutCode}`.trim();
                console.log('CountryPhoneSelector: Fallback - Phone updated to:', phoneInput.value);
            }
        });
        
        // Set default Saudi Arabia
        const saudiOption = Array.from(countrySelect.options).find(option => 
            option.textContent.includes('Saudi Arabia') || option.getAttribute('data-code') === '966'
        );
        
        if (saudiOption) {
            saudiOption.selected = true;
            const countryCode = saudiOption.getAttribute('data-code');
            if (countryCode && !phoneInput.value.trim()) {
                phoneInput.value = `+${countryCode} `;
                console.log('CountryPhoneSelector: Fallback - Default phone set to:', phoneInput.value);
            }
        }
    }
}, 1000);