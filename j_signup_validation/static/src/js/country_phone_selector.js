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
            
            // Initial phone preview update
            this.updatePhonePreview();
        }

        setDefaultCountry() {
            // Set Saudi Arabia as default
            const saudiOption = Array.from(this.countrySelect.options).find(option => 
                option.textContent.includes('Saudi Arabia') || option.getAttribute('data-code') === '966'
            );
            
            if (saudiOption) {
                saudiOption.selected = true;
                // Auto-populate phone field with country code if empty
                if (!this.phoneInput.value.trim()) {
                    this.phoneInput.value = '+966 ';
                }
                this.updatePhonePreview();
            }
        }

        handleCountryChange(event) {
            const selectedOption = event.target.selectedOptions[0];
            const countryCode = selectedOption ? selectedOption.getAttribute('data-code') : '';
            
            if (countryCode) {
                const currentPhone = this.phoneInput.value.trim();
                let phoneWithoutCode = currentPhone;
                
                // Remove existing country code if present
                if (currentPhone.startsWith('+')) {
                    phoneWithoutCode = currentPhone.replace(/^\+\d{1,4}\s*/, '').trim();
                }
                
                // Set new phone value with country code
                const newPhoneValue = phoneWithoutCode ? `+${countryCode} ${phoneWithoutCode}` : `+${countryCode} `;
                this.phoneInput.value = newPhoneValue;
            }
            
            this.updatePhonePreview();
            
            // Re-validate phone number when country changes
            if (this.phoneInput.value.trim()) {
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
            const phoneNumber = this.phoneInput.value.trim();
            this.phonePreview.textContent = phoneNumber || '+966 ';
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