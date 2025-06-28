/**
 * Signup Form Validation Module
 * Handles real-time validation for email, phone, and form submission
 */

(function() {
    'use strict';

    // Main validation controller
    class SignupValidator {
        constructor() {
            this.form = document.getElementById('signupForm');
            this.emailInput = document.getElementById('email');
            this.phoneInput = document.getElementById('phone');
            this.passwordInput = document.getElementById('password');
            this.confirmPasswordInput = document.getElementById('confirm_password');
            this.submitBtn = document.getElementById('submitBtn');
            
            this.validationRules = window.signupValidationRules || {};
            this.validationTimeouts = {};
            this.validationStates = {
                email: false,
                phone: false,
                password: false,
                confirmPassword: false,
                firstName: false,
                lastName: false
            };

            this.init();
        }

        init() {
            if (!this.form) {
                console.warn('Signup form not found');
                return;
            }

            this.bindEvents();
            this.initValidation();
            console.log('Signup validation initialized');
        }

        bindEvents() {
            // Form submission
            this.form.addEventListener('submit', this.handleFormSubmit.bind(this));

            // Real-time validation
            this.emailInput?.addEventListener('input', this.handleEmailInput.bind(this));
            this.emailInput?.addEventListener('blur', this.handleEmailBlur.bind(this));

            this.phoneInput?.addEventListener('input', this.handlePhoneInput.bind(this));
            this.phoneInput?.addEventListener('blur', this.handlePhoneBlur.bind(this));

            this.passwordInput?.addEventListener('input', this.handlePasswordInput.bind(this));
            this.confirmPasswordInput?.addEventListener('input', this.handleConfirmPasswordInput.bind(this));

            // Name validation
            document.getElementById('first_name')?.addEventListener('input', this.handleNameInput.bind(this));
            document.getElementById('last_name')?.addEventListener('input', this.handleNameInput.bind(this));

            // Show/hide password toggle
            this.addPasswordToggle();
        }

        initValidation() {
            // Set initial validation states
            this.updateSubmitButton();
        }

        // Email validation
        handleEmailInput(event) {
            const email = event.target.value.trim();
            
            // Clear previous timeout
            if (this.validationTimeouts.email) {
                clearTimeout(this.validationTimeouts.email);
            }

            // Show loading state
            this.setEmailValidationStatus('checking', 'Checking email...');
            event.target.classList.add('loading');

            // Debounced validation
            this.validationTimeouts.email = setTimeout(() => {
                this.validateEmail(email);
            }, 500);
        }

        handleEmailBlur(event) {
            const email = event.target.value.trim();
            if (email) {
                this.validateEmail(email);
            }
        }

        async validateEmail(email) {
            try {
                if (!email) {
                    this.setEmailValidationStatus('', '');
                    this.validationStates.email = false;
                    this.updateSubmitButton();
                    return;
                }

                // Basic format validation first
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    this.setEmailValidationStatus('invalid', 'Invalid email format');
                    this.validationStates.email = false;
                    this.updateSubmitButton();
                    return;
                }

                // Server-side validation
                const response = await this.makeAjaxRequest('/web/signup/validate_email', { email });
                
                this.emailInput.classList.remove('loading');

                if (response.valid) {
                    this.setEmailValidationStatus('valid', 'Email is valid');
                    this.validationStates.email = true;
                } else {
                    const message = response.messages.join(', ');
                    this.setEmailValidationStatus('invalid', message);
                    this.validationStates.email = false;
                }

            } catch (error) {
                console.error('Email validation error:', error);
                this.setEmailValidationStatus('invalid', 'Email validation failed');
                this.validationStates.email = false;
            }

            this.updateSubmitButton();
        }

        setEmailValidationStatus(status, message) {
            const statusElement = document.querySelector('.email-validation-status');
            const emailInput = this.emailInput;

            if (statusElement) {
                statusElement.textContent = message;
                statusElement.className = `email-validation-status ${status}`;
            }

            // Update input visual state
            emailInput.classList.remove('is-valid', 'is-invalid');
            if (status === 'valid') {
                emailInput.classList.add('is-valid');
            } else if (status === 'invalid') {
                emailInput.classList.add('is-invalid');
            }
        }

        // Phone validation
        handlePhoneInput(event) {
            const phone = event.target.value.trim();
            
            // Clear previous timeout
            if (this.validationTimeouts.phone) {
                clearTimeout(this.validationTimeouts.phone);
            }

            // Show loading state
            this.setPhoneValidationStatus('checking', 'Validating phone...');
            event.target.classList.add('loading');

            // Debounced validation
            this.validationTimeouts.phone = setTimeout(() => {
                this.validatePhone(phone);
            }, 500);
        }

        handlePhoneBlur(event) {
            const phone = event.target.value.trim();
            if (phone) {
                this.validatePhone(phone);
            }
        }

        async validatePhone(phone) {
            try {
                if (!phone) {
                    this.setPhoneValidationStatus('', '');
                    this.validationStates.phone = false;
                    this.updateSubmitButton();
                    return;
                }

                // Server-side validation
                const response = await this.makeAjaxRequest('/web/signup/validate_phone', { phone });
                
                this.phoneInput.classList.remove('loading');

                if (response.valid) {
                    this.setPhoneValidationStatus('valid', `Valid: ${response.formatted}`);
                    this.validationStates.phone = true;
                    // Update input with formatted number
                    if (response.formatted && response.formatted !== phone) {
                        this.phoneInput.value = response.formatted;
                    }
                } else {
                    const message = response.messages.join(', ');
                    this.setPhoneValidationStatus('invalid', message);
                    this.validationStates.phone = false;
                }

            } catch (error) {
                console.error('Phone validation error:', error);
                this.setPhoneValidationStatus('invalid', 'Phone validation failed');
                this.validationStates.phone = false;
            }

            this.updateSubmitButton();
        }

        setPhoneValidationStatus(status, message) {
            const statusElement = document.querySelector('.phone-validation-status');
            const phoneInput = this.phoneInput;

            if (statusElement) {
                statusElement.textContent = message;
                statusElement.className = `phone-validation-status ${status}`;
            }

            // Update input visual state
            phoneInput.classList.remove('is-valid', 'is-invalid');
            if (status === 'valid') {
                phoneInput.classList.add('is-valid');
            } else if (status === 'invalid') {
                phoneInput.classList.add('is-invalid');
            }
        }

        // Password confirmation validation
        handlePasswordInput(event) {
            this.validationStates.password = event.target.value.length > 0;
            this.validatePasswordConfirmation();
            this.updateSubmitButton();
        }

        handleConfirmPasswordInput(event) {
            this.validatePasswordConfirmation();
            this.updateSubmitButton();
        }

        validatePasswordConfirmation() {
            const password = this.passwordInput?.value || '';
            const confirmPassword = this.confirmPasswordInput?.value || '';
            const confirmInput = this.confirmPasswordInput;

            if (!confirmPassword) {
                this.validationStates.confirmPassword = false;
                confirmInput.classList.remove('is-valid', 'is-invalid');
                return;
            }

            if (password === confirmPassword) {
                this.validationStates.confirmPassword = true;
                confirmInput.classList.remove('is-invalid');
                confirmInput.classList.add('is-valid');
                this.setInputFeedback(confirmInput, 'Passwords match', 'valid');
            } else {
                this.validationStates.confirmPassword = false;
                confirmInput.classList.remove('is-valid');
                confirmInput.classList.add('is-invalid');
                this.setInputFeedback(confirmInput, 'Passwords do not match', 'invalid');
            }
        }

        // Name validation
        handleNameInput(event) {
            const input = event.target;
            const value = input.value.trim();
            const fieldName = input.id === 'first_name' ? 'firstName' : 'lastName';

            if (value.length >= 2) {
                this.validationStates[fieldName] = true;
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                this.validationStates[fieldName] = false;
                input.classList.remove('is-valid');
                if (value.length > 0) {
                    input.classList.add('is-invalid');
                }
            }

            this.updateSubmitButton();
        }

        // Form submission
        async handleFormSubmit(event) {
            event.preventDefault();

            // Final validation check
            if (!this.isFormValid()) {
                this.showFormErrors();
                return;
            }

            // Show loading state
            this.setSubmitButtonLoading(true);

            try {
                // Submit form data
                const formData = new FormData(this.form);
                const response = await fetch(this.form.action, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    // Handle successful registration
                    window.location.href = response.url;
                } else {
                    // Handle server errors
                    const errorText = await response.text();
                    this.showError('Registration failed. Please try again.');
                    console.error('Registration error:', errorText);
                }

            } catch (error) {
                console.error('Form submission error:', error);
                this.showError('Network error. Please check your connection and try again.');
            } finally {
                this.setSubmitButtonLoading(false);
            }
        }

        // Utility methods
        isFormValid() {
            return Object.values(this.validationStates).every(state => state === true);
        }

        updateSubmitButton() {
            const isValid = this.isFormValid();
            this.submitBtn.disabled = !isValid;
            
            if (isValid) {
                this.submitBtn.classList.remove('btn-secondary');
                this.submitBtn.classList.add('btn-primary');
            } else {
                this.submitBtn.classList.remove('btn-primary');
                this.submitBtn.classList.add('btn-secondary');
            }
        }

        setSubmitButtonLoading(loading) {
            if (loading) {
                this.submitBtn.classList.add('loading');
                this.submitBtn.disabled = true;
                this.submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Creating Account...';
            } else {
                this.submitBtn.classList.remove('loading');
                this.submitBtn.disabled = !this.isFormValid();
                this.submitBtn.innerHTML = '<i class="fa fa-user-plus me-2"></i>Create Account';
            }
        }

        setInputFeedback(input, message, type) {
            let feedback = input.parentNode.querySelector('.invalid-feedback, .valid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = type === 'valid' ? 'valid-feedback' : 'invalid-feedback';
                input.parentNode.appendChild(feedback);
            }
            feedback.textContent = message;
            feedback.className = type === 'valid' ? 'valid-feedback' : 'invalid-feedback';
        }

        showFormErrors() {
            const errors = [];
            
            if (!this.validationStates.firstName) errors.push('First name is required');
            if (!this.validationStates.lastName) errors.push('Last name is required');
            if (!this.validationStates.email) errors.push('Valid email is required');
            if (!this.validationStates.phone) errors.push('Valid phone number is required');
            if (!this.validationStates.password) errors.push('Password is required');
            if (!this.validationStates.confirmPassword) errors.push('Password confirmation is required');

            this.showError(errors.join(', '));
        }

        showError(message) {
            // Create or update error alert
            let alert = document.querySelector('.alert-danger');
            if (!alert) {
                alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.innerHTML = `
                    <i class="fa fa-exclamation-triangle me-2"></i>
                    <span class="error-message"></span>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                this.form.insertBefore(alert, this.form.firstChild);
            }
            
            alert.querySelector('.error-message').textContent = message;
            alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        addPasswordToggle() {
            const passwordInputs = [this.passwordInput, this.confirmPasswordInput];
            
            passwordInputs.forEach(input => {
                if (!input) return;
                
                const wrapper = input.parentNode;
                const toggle = document.createElement('button');
                toggle.type = 'button';
                toggle.className = 'btn btn-outline-secondary password-toggle';
                toggle.innerHTML = '<i class="fa fa-eye"></i>';
                toggle.style.cssText = `
                    position: absolute;
                    right: 10px;
                    top: 50%;
                    transform: translateY(-50%);
                    z-index: 5;
                    border: none;
                    background: transparent;
                    padding: 0.25rem 0.5rem;
                    font-size: 0.875rem;
                `;
                
                toggle.addEventListener('click', () => {
                    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                    input.setAttribute('type', type);
                    
                    const icon = toggle.querySelector('i');
                    icon.className = type === 'password' ? 'fa fa-eye' : 'fa fa-eye-slash';
                });
                
                wrapper.style.position = 'relative';
                wrapper.appendChild(toggle);
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
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error.message || 'Server error');
            }
            
            return result.result;
        }
    }

    // Initialize signup validation
    function initSignupValidation() {
        const form = document.getElementById('signupForm');
        
        if (!form) {
            console.warn('Signup form not found');
            return;
        }

        // Create and initialize validator
        const validator = new SignupValidator();

        console.log('Signup form validation initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSignupValidation);
    } else {
        initSignupValidation();
    }

    // Export for testing purposes
    window.SignupValidator = SignupValidator;

})();