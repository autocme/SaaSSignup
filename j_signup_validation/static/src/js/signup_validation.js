/**
 * Signup Form Validation Module
 * Handles real-time validation for email, phone, and form submission
 */

(function() {
    'use strict';

    // Multi-step form controller
    class MultiStepController {
        constructor() {
            this.currentStep = 1;
            this.totalSteps = 3;
            this.steps = document.querySelectorAll('.form-step');
            this.stepItems = document.querySelectorAll('.step-item');
            this.hasDynamicFields = document.querySelectorAll('.dynamic-field').length > 0;
            
            this.init();
        }

        init() {
            this.bindNavigationEvents();
            this.updateStepDisplay();
            this.updateProgressIndicator();
            
            // If no dynamic fields, show only 2 steps
            if (!this.hasDynamicFields) {
                this.totalSteps = 2;
                this.hideStep3();
            }
        }

        bindNavigationEvents() {
            // Step 1 Next
            const nextBtn1 = document.getElementById('nextBtn1');
            if (nextBtn1) {
                nextBtn1.addEventListener('click', () => this.goToStep(2));
            }

            // Step 2 Previous/Next
            const prevBtn2 = document.getElementById('prevBtn2');
            const nextBtn2 = document.getElementById('nextBtn2');
            if (prevBtn2) {
                prevBtn2.addEventListener('click', () => this.goToStep(1));
            }
            if (nextBtn2) {
                nextBtn2.addEventListener('click', () => {
                    if (this.hasDynamicFields) {
                        this.goToStep(3);
                    } else {
                        this.submitForm();
                    }
                });
            }

            // Step 3 Previous (if dynamic fields exist)
            const prevBtn3 = document.getElementById('prevBtn3');
            const prevBtn2Final = document.getElementById('prevBtn2Final');
            if (prevBtn3) {
                prevBtn3.addEventListener('click', () => this.goToStep(2));
            }
            if (prevBtn2Final) {
                prevBtn2Final.addEventListener('click', () => this.goToStep(1));
            }
        }

        goToStep(stepNumber) {
            // Validate current step before moving forward
            if (stepNumber > this.currentStep && !this.validateCurrentStep()) {
                return;
            }

            this.currentStep = stepNumber;
            this.updateStepDisplay();
            this.updateProgressIndicator();
        }

        updateStepDisplay() {
            this.steps.forEach((step, index) => {
                step.classList.toggle('active', index + 1 === this.currentStep);
            });

            // Handle final buttons for step 2 when no dynamic fields
            const step2Final = document.getElementById('step-2-final');
            if (step2Final) {
                step2Final.classList.toggle('active', this.currentStep === 2 && !this.hasDynamicFields);
            }
        }

        updateProgressIndicator() {
            this.stepItems.forEach((item, index) => {
                const stepNum = index + 1;
                item.classList.toggle('active', stepNum === this.currentStep);
                item.classList.toggle('completed', stepNum < this.currentStep);
            });
        }

        hideStep3() {
            const step3Item = document.querySelector('.step-item:nth-child(3)');
            if (step3Item) {
                step3Item.style.display = 'none';
            }
        }

        validateCurrentStep() {
            if (this.currentStep === 1) {
                return window.signupValidator ? window.signupValidator.validateStep1() : true;
            } else if (this.currentStep === 2) {
                return window.signupValidator ? window.signupValidator.validateStep2() : true;
            }
            return true;
        }

        submitForm() {
            const form = document.getElementById('signupForm');
            if (form && window.signupValidator && window.signupValidator.isFormValid()) {
                form.submit();
            }
        }
    }

    // Main validation controller
    class SignupValidator {
        constructor() {
            this.form = document.getElementById('signupForm');
            this.emailInput = document.getElementById('email');
            this.phoneInput = document.getElementById('phone');
            this.passwordInput = document.getElementById('password');
            this.confirmPasswordInput = document.getElementById('confirm_password');
            this.submitBtn = document.getElementById('submitBtn');
            this.accountTypeRadios = document.querySelectorAll('input[name="account_type"]');
            this.vatCrField = document.getElementById('vat_cr_field');
            this.vatCrInput = document.getElementById('vat_cr_number');
            this.individualNameFields = document.getElementById('individual_name_fields');
            this.companyNameField = document.getElementById('company_name_field');
            this.companyNameInput = document.getElementById('company_name');

            this.validationRules = window.signupValidationRules || {};
            this.validationTimeouts = {};
            this.validationStates = {
                email: false,
                phone: false,
                password: false,
                confirmPassword: false,
                firstName: false,
                lastName: false,
                companyName: true, // Default true for individual, false for company
                vatCr: true // Default true for individual, false for company
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
            this.initializeAccountTypeValidation();
            console.log('Signup validation initialized');
        }

        initializeAccountTypeValidation() {
            // Initialize validation states based on the default account type
            const accountType = document.querySelector('input[name="account_type"]:checked')?.value || 'individual';
            
            console.log('initializeAccountTypeValidation - Account type:', accountType);
            console.log('initializeAccountTypeValidation - Before setting validation states:', this.validationStates);
            
            if (accountType === 'company') {
                // For company accounts, name fields are not required
                this.validationStates.firstName = true;
                this.validationStates.lastName = true;
                this.validationStates.companyName = false;
                this.validationStates.vatCr = false;
                
                // Remove required attributes from name fields
                document.getElementById('first_name')?.removeAttribute('required');
                document.getElementById('last_name')?.removeAttribute('required');
                
                // Add required attributes to company fields
                document.getElementById('company_name')?.setAttribute('required', 'required');
                document.getElementById('vat_cr_number')?.setAttribute('required', 'required');
            } else {
                // For individual accounts, name fields are required
                this.validationStates.firstName = false;
                this.validationStates.lastName = false;
                this.validationStates.companyName = true;
                this.validationStates.vatCr = true;
                
                // Add required attributes to name fields
                document.getElementById('first_name')?.setAttribute('required', 'required');
                document.getElementById('last_name')?.setAttribute('required', 'required');
                
                // Remove required attributes from company fields
                document.getElementById('company_name')?.removeAttribute('required');
                document.getElementById('vat_cr_number')?.removeAttribute('required');
            }
            
            console.log('initializeAccountTypeValidation - After setting validation states:', this.validationStates);
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

            // Company name validation
            this.companyNameInput?.addEventListener('input', this.handleCompanyNameInput.bind(this));

            // Account type changes
            this.accountTypeRadios.forEach(radio => {
                radio.addEventListener('change', this.handleAccountTypeChange.bind(this));
            });

            // VAT/CR validation
            this.vatCrInput?.addEventListener('input', this.handleVatCrInput.bind(this));

            // Dynamic fields validation
            this.bindDynamicFieldEvents();

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
                const response = await this.makeAjaxRequest('/j_signup_validation/validate_email', { email });

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

                // Get selected country ID
                const countrySelect = document.getElementById('phone_country');
                const countryId = countrySelect ? countrySelect.value : null;

                console.log('Phone validation - Phone:', phone, 'Country ID:', countryId);

                // Server-side validation with country ID
                const response = await this.makeAjaxRequest('/j_signup_validation/validate_phone', { 
                    phone: phone,
                    country_id: countryId 
                });

                this.phoneInput.classList.remove('loading');

                if (response.valid) {
                    this.setPhoneValidationStatus('valid', 'Phone is valid');
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
                // For password fields, use custom class instead of is-valid to avoid check symbols
                confirmInput.classList.add('is-valid'); 
                // Note: CSS will override to show only green border, no check symbol
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

            if (value.length >= 1) {
                this.validationStates[fieldName] = true;
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                this.validationStates[fieldName] = false;
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }

            this.updateSubmitButton();
        }

        // Account type change handler
        handleAccountTypeChange(event) {
            const accountType = event.target.value;
            
            console.log('handleAccountTypeChange - Account type:', accountType);
            console.log('handleAccountTypeChange - Before change validation states:', this.validationStates);

            if (accountType === 'company') {
                // Hide individual name fields
                this.individualNameFields.style.display = 'none';
                
                // Show company name field with animation and make it required
                this.companyNameField.style.display = 'block';
                setTimeout(() => {
                    this.companyNameField.classList.add('show');
                }, 10);
                this.companyNameInput.setAttribute('required', 'required');
                this.validationStates.companyName = false; // Reset validation state

                // Show VAT/CR field with animation and make it required
                this.vatCrField.style.display = 'block';
                setTimeout(() => {
                    this.vatCrField.classList.add('show');
                }, 10);
                this.vatCrInput.setAttribute('required', 'required');
                this.validationStates.vatCr = false; // Reset validation state

                // Clear individual name requirements and reset validation states
                document.getElementById('first_name')?.removeAttribute('required');
                document.getElementById('last_name')?.removeAttribute('required');
                // Clear validation classes from name fields
                document.getElementById('first_name')?.classList.remove('is-valid', 'is-invalid');
                document.getElementById('last_name')?.classList.remove('is-valid', 'is-invalid');
                // Set name fields as valid for company accounts (they're not required)
                this.validationStates.firstName = true;
                this.validationStates.lastName = true;

                // Validate if there's already a value
                if (this.companyNameInput.value.trim()) {
                    this.validateCompanyName(this.companyNameInput.value.trim());
                }
                if (this.vatCrInput.value.trim()) {
                    this.validateVatCr(this.vatCrInput.value.trim());
                }
            } else {
                // Show individual name fields with proper Bootstrap row layout
                this.individualNameFields.style.display = '';
                
                // Hide company name field with animation and remove requirement
                this.companyNameField.classList.remove('show');
                setTimeout(() => {
                    this.companyNameField.style.display = 'none';
                }, 300);
                this.companyNameInput.removeAttribute('required');
                this.companyNameInput.classList.remove('is-valid', 'is-invalid');
                this.validationStates.companyName = true; // Valid for individual

                // Hide VAT/CR field with animation and remove requirement
                this.vatCrField.classList.remove('show');
                setTimeout(() => {
                    this.vatCrField.style.display = 'none';
                }, 300);
                this.vatCrInput.removeAttribute('required');
                this.vatCrInput.classList.remove('is-valid', 'is-invalid');
                this.validationStates.vatCr = true; // Valid for individual

                // Set individual name requirements
                document.getElementById('first_name')?.setAttribute('required', 'required');
                document.getElementById('last_name')?.setAttribute('required', 'required');
                this.validationStates.firstName = false;
                this.validationStates.lastName = false;

                // Re-validate name fields if they have values
                const firstNameInput = document.getElementById('first_name');
                const lastNameInput = document.getElementById('last_name');
                if (firstNameInput && firstNameInput.value.trim()) {
                    this.handleNameInput({target: firstNameInput});
                }
                if (lastNameInput && lastNameInput.value.trim()) {
                    this.handleNameInput({target: lastNameInput});
                }
            }

            console.log('handleAccountTypeChange - After change validation states:', this.validationStates);
            this.updateSubmitButton();
        }

        // Company name validation
        handleCompanyNameInput(event) {
            const value = event.target.value.trim();
            this.validateCompanyName(value);
            this.updateSubmitButton();
        }

        // VAT/CR validation
        handleVatCrInput(event) {
            const value = event.target.value.trim();
            this.validateVatCr(value);
            this.updateSubmitButton();
        }

        validateCompanyName(value) {
            const input = this.companyNameInput;

            if (!value) {
                this.validationStates.companyName = false;
                input.classList.remove('is-valid', 'is-invalid');
                return;
            }

            // Company name validation (at least 2 characters)
            if (value.length >= 2) {
                this.validationStates.companyName = true;
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                this.validationStates.companyName = false;
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        }

        validateVatCr(value) {
            const input = this.vatCrInput;

            if (!value) {
                this.validationStates.vatCr = false;
                input.classList.remove('is-valid', 'is-invalid');
                return;
            }

            // Basic VAT/CR validation (at least 10 characters, alphanumeric)
            const vatCrRegex = /^[A-Za-z0-9]{10,}$/;

            if (vatCrRegex.test(value)) {
                this.validationStates.vatCr = true;
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
                this.setInputFeedback(input, 'VAT/CR number format is valid', 'valid');
            } else {
                this.validationStates.vatCr = false;
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                this.setInputFeedback(input, 'VAT/CR number must be at least 10 alphanumeric characters', 'invalid');
            }
        }



        // Form submission
        async handleFormSubmit(event) {
            event.preventDefault();

            // Prevent multiple submissions
            if (this.form.dataset.submitting === 'true') {
                console.log('Form already submitting, preventing duplicate submission');
                return;
            }

            // Final validation check
            if (!this.isFormValid()) {
                this.showFormErrors();
                return;
            }

            // Mark form as submitting to prevent duplicates
            this.form.dataset.submitting = 'true';

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
                    // Handle successful registration - DO NOT reset flag to prevent duplicate submissions
                    console.log('Registration successful, redirecting...');
                    window.location.href = response.url;
                    // Form submission flag stays 'true' to prevent any further submissions
                } else {
                    // Handle server errors
                    const errorText = await response.text();
                    this.showError('Registration failed. Please try again.');
                    console.error('Registration error:', errorText);
                    // Reset submission flag to allow retry only on errors
                    this.form.dataset.submitting = 'false';
                    this.setSubmitButtonLoading(false);
                }

            } catch (error) {
                console.error('Form submission error:', error);
                this.showError('Network error. Please check your connection and try again.');
                // Reset submission flag to allow retry only on errors
                this.form.dataset.submitting = 'false';
                this.setSubmitButtonLoading(false);
            }
        }

        // Utility methods
        getSelectedAccountType() {
            const selectedRadio = document.querySelector('input[name="account_type"]:checked');
            return selectedRadio ? selectedRadio.value : 'individual';
        }

        isFormValid() {
            // Get current account type
            const accountType = this.getSelectedAccountType();
            
            // Create validation requirements based on account type
            const requiredFields = ['email', 'phone', 'password', 'confirmPassword'];
            
            if (accountType === 'individual') {
                requiredFields.push('firstName', 'lastName');
            } else if (accountType === 'company') {
                requiredFields.push('companyName');
                // Check if VAT/CR field is required for companies
                const vatCrInput = document.getElementById('vat_cr_number');
                if (vatCrInput && vatCrInput.hasAttribute('required')) {
                    requiredFields.push('vatCr');
                }
            }
            
            console.log('isFormValid - Account type:', accountType);
            console.log('isFormValid - Required fields:', requiredFields);
            console.log('isFormValid - Validation states:', this.validationStates);
            
            // Check only required fields based on account type
            const basicValidation = requiredFields.every(field => {
                const isValid = this.validationStates[field] === true;
                console.log(`isFormValid - Field ${field}: ${isValid}`);
                return isValid;
            });

            // Check dynamic required fields
            const dynamicValidation = this.validateDynamicFields();

            console.log('isFormValid - Basic validation:', basicValidation);
            console.log('isFormValid - Dynamic validation:', dynamicValidation);
            console.log('isFormValid - Overall valid:', basicValidation && dynamicValidation);

            return basicValidation && dynamicValidation;
        }

        validateDynamicFields() {
            // Get all dynamic fields that are marked as required
            const requiredDynamicFields = this.form.querySelectorAll('[id^="dynamic_"][required]');
            
            console.log(`Found ${requiredDynamicFields.length} required dynamic fields`);

            for (let field of requiredDynamicFields) {
                const value = field.value.trim();
                console.log(`Dynamic field ${field.id}: value="${value}", valid=${!!value}`);

                // Check if field has value - no visual feedback, just return validation state
                if (!value) {
                    console.log(`Dynamic field validation failed for ${field.id}`);
                    return false;
                }
            }

            console.log('All dynamic fields validation passed');
            return true;
        }

        validateStep1() {
            const accountType = this.getSelectedAccountType();
            console.log('validateStep1 - Account type:', accountType);
            
            // Basic fields required for all accounts
            const basicValid = this.validationStates.email && this.validationStates.phone;
            console.log('validateStep1 - Basic validation (email, phone):', basicValid);
            
            // Account type specific validation
            let accountTypeValid = true;
            if (accountType === 'individual') {
                accountTypeValid = this.validationStates.firstName && this.validationStates.lastName;
                console.log('validateStep1 - Individual name validation:', accountTypeValid);
            } else if (accountType === 'company') {
                accountTypeValid = this.validationStates.companyName && this.validationStates.vatCr;
                console.log('validateStep1 - Company validation:', accountTypeValid);
            }
            
            const step1Valid = basicValid && accountTypeValid;
            console.log('validateStep1 - Overall valid:', step1Valid);
            return step1Valid;
        }

        validateStep2() {
            const passwordValid = this.validationStates.password && this.validationStates.confirmPassword;
            console.log('validateStep2 - Password validation:', passwordValid);
            return passwordValid;
        }

        bindDynamicFieldEvents() {
            // Get all dynamic fields and add event listeners
            const dynamicFields = this.form.querySelectorAll('[id^="dynamic_"]');

            dynamicFields.forEach(field => {
                // Add input event listener for real-time validation
                field.addEventListener('input', (event) => {
                    this.handleDynamicFieldInput(event);
                });

                // Add blur event listener for validation on focus loss
                field.addEventListener('blur', (event) => {
                    this.handleDynamicFieldBlur(event);
                });
            });
        }

        handleDynamicFieldInput(event) {
            // Simply update submit button state - no visual feedback on the field itself
            this.updateSubmitButton();
        }

        handleDynamicFieldBlur(event) {
            // Same validation as input, ensures validation on focus loss
            this.handleDynamicFieldInput(event);
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
            const accountType = this.getSelectedAccountType();

            console.log('showFormErrors - Account type:', accountType);
            console.log('showFormErrors - Validation states:', this.validationStates);

            // Only check name fields based on account type
            if (accountType === 'individual') {
                if (!this.validationStates.firstName) errors.push('First name is required');
                if (!this.validationStates.lastName) errors.push('Last name is required');
            } else if (accountType === 'company') {
                if (!this.validationStates.companyName) errors.push('Company name is required');
            }

            // Common required fields for all account types
            if (!this.validationStates.email) errors.push('Valid email is required');
            if (!this.validationStates.phone) errors.push('Valid phone number is required');
            if (!this.validationStates.password) errors.push('Password is required');
            if (!this.validationStates.confirmPassword) errors.push('Password confirmation is required');

            // Don't show dynamic field errors - they behave silently like confirm password

            if (errors.length > 0) {
                this.showError(errors.join(', '));
            }
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
            // Only add toggle button to confirm password field
            const input = this.confirmPasswordInput;

            if (!input) return;

            const wrapper = input.parentNode;

            // Add proper CSS classes
            wrapper.classList.add('password-field-container', 'position-relative');
            input.classList.add('password-input-with-toggle');

            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'password-toggle-btn';
            toggle.innerHTML = '<i class="fa fa-eye"></i>';

            toggle.addEventListener('click', () => {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);

                const icon = toggle.querySelector('i');
                icon.className = type === 'password' ? 'fa fa-eye' : 'fa fa-eye-slash';
            });

            // Add toggle button to confirm password field
            wrapper.appendChild(toggle);
            console.log('Password toggle added for confirm password field only:', toggle);
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
        
        // Create and initialize multi-step controller
        const multiStepController = new MultiStepController();
        
        // Expose globally for country phone selector integration
        window.signupValidator = validator;
        window.multiStepController = multiStepController;

        console.log('Signup form validation and multi-step controller initialized');
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