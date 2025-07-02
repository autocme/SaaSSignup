/**
 * Password Strength Validation Module
 * Provides real-time password strength validation and visual feedback
 */

(function() {
    'use strict';

    // Password strength calculator
    class PasswordStrengthValidator {
        constructor(rules) {
            this.rules = rules || {};
            this.minLength = this.rules.min_length || 8;
            this.requireNumber = this.rules.require_number || false;
            this.requireUppercase = this.rules.require_uppercase || false;
            this.requireLowercase = this.rules.require_lowercase || false;
            this.requireSpecial = this.rules.require_special || false;
        }

        /**
         * Calculate password strength score (0-100)
         * @param {string} password - Password to evaluate
         * @returns {Object} - Validation result
         */
        validatePassword(password) {
            if (!password) {
                return {
                    score: 0,
                    level: 'very-weak',
                    label: 'Very Weak',
                    requirements: this.getRequirements(password),
                    valid: false
                };
            }

            let score = 0;
            const requirements = this.getRequirements(password);
            const metRequirements = requirements.filter(req => req.met).length;
            const totalRequirements = requirements.length;

            // Base score from meeting requirements
            score = (metRequirements / totalRequirements) * 80;

            // Bonus points for length beyond minimum
            if (password.length > this.minLength) {
                score += Math.min(20, (password.length - this.minLength) * 2);
            }

            // Penalty for common patterns
            score -= this.checkCommonPatterns(password);

            // Ensure score is within bounds
            score = Math.max(0, Math.min(100, Math.round(score)));

            return {
                score: score,
                level: this.getStrengthLevel(score),
                label: this.getStrengthLabel(score),
                requirements: requirements,
                valid: metRequirements === totalRequirements
            };
        }

        /**
         * Get requirements status
         * @param {string} password - Password to check
         * @returns {Array} - Array of requirement objects
         */
        getRequirements(password) {
            const requirements = [];

            // Length requirement
            requirements.push({
                id: 'length',
                text: `At least ${this.minLength} characters`,
                met: password.length >= this.minLength
            });

            // Number requirement
            if (this.requireNumber) {
                requirements.push({
                    id: 'number',
                    text: 'At least one number',
                    met: /\d/.test(password)
                });
            }

            // Uppercase requirement
            if (this.requireUppercase) {
                requirements.push({
                    id: 'uppercase',
                    text: 'At least one uppercase letter',
                    met: /[A-Z]/.test(password)
                });
            }

            // Lowercase requirement
            if (this.requireLowercase) {
                requirements.push({
                    id: 'lowercase',
                    text: 'At least one lowercase letter',
                    met: /[a-z]/.test(password)
                });
            }

            // Special character requirement
            if (this.requireSpecial) {
                requirements.push({
                    id: 'special',
                    text: 'At least one special character',
                    met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\?]/.test(password)
                });
            }

            return requirements;
        }

        /**
         * Check for common weak patterns
         * @param {string} password - Password to check
         * @returns {number} - Penalty score
         */
        checkCommonPatterns(password) {
            let penalty = 0;
            const lower = password.toLowerCase();

            // Common patterns
            const commonPatterns = [
                /(.)\1{2,}/, // Repeated characters
                /123|abc|qwerty|password|admin/i, // Common sequences
                /^\d+$/, // Only numbers
                /^[a-zA-Z]+$/ // Only letters
            ];

            commonPatterns.forEach(pattern => {
                if (pattern.test(password)) {
                    penalty += 10;
                }
            });

            // Sequential characters penalty
            if (this.hasSequentialChars(password)) {
                penalty += 5;
            }

            return penalty;
        }

        /**
         * Check for sequential characters
         * @param {string} password - Password to check
         * @returns {boolean} - Has sequential characters
         */
        hasSequentialChars(password) {
            for (let i = 0; i < password.length - 2; i++) {
                const char1 = password.charCodeAt(i);
                const char2 = password.charCodeAt(i + 1);
                const char3 = password.charCodeAt(i + 2);

                if (char2 === char1 + 1 && char3 === char2 + 1) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Get strength level based on score
         * @param {number} score - Password score
         * @returns {string} - Strength level
         */
        getStrengthLevel(score) {
            if (score < 20) return 'very-weak';
            if (score < 40) return 'weak';
            if (score < 60) return 'fair';
            if (score < 80) return 'good';
            return 'strong';
        }

        /**
         * Get strength label based on score
         * @param {number} score - Password score
         * @returns {string} - Strength label
         */
        getStrengthLabel(score) {
            if (score < 20) return 'Very Weak';
            if (score < 40) return 'Weak';
            if (score < 60) return 'Fair';
            if (score < 80) return 'Good';
            return 'Strong';
        }
    }

    // Password strength UI controller
    class PasswordStrengthUI {
        constructor(passwordInput, validator) {
            this.passwordInput = passwordInput;
            this.validator = validator;
            this.container = this.passwordInput.parentNode.querySelector('.j-password-strength');
            
            if (this.container) {
                this.progressBar = this.container.querySelector('.j-strength-progress');
                this.strengthLabel = this.container.querySelector('.j-strength-label');
                this.requirementsList = this.container.querySelector('.j-password-requirements');
                this.init();
            } else {
                console.warn('Password strength container not found');
            }
        }

        init() {
            // Bind events
            this.passwordInput.addEventListener('input', this.handlePasswordInput.bind(this));
            this.passwordInput.addEventListener('focus', this.handlePasswordFocus.bind(this));
            this.passwordInput.addEventListener('blur', this.handlePasswordBlur.bind(this));

            // Initial state
            this.updateUI(this.validator.validatePassword(''));
        }

        handlePasswordInput(event) {
            const password = event.target.value;
            const result = this.validator.validatePassword(password);
            this.updateUI(result);
            
            // Update form validation
            this.updateFormValidation(result);
        }

        handlePasswordFocus(event) {
            this.container.style.display = 'block';
            this.container.style.opacity = '1';
        }

        handlePasswordBlur(event) {
            // Keep visible if password has content
            if (!event.target.value) {
                this.container.style.opacity = '0.7';
            }
        }

        updateUI(result) {
            // Update progress bar with new CSS classes
            this.progressBar.style.width = `${result.score}%`;
            this.progressBar.className = `j-strength-progress j-strength-${result.level}`;

            // Update strength label (if exists)
            if (this.strengthLabel) {
                this.strengthLabel.textContent = result.label;
                this.strengthLabel.className = `j-strength-label j-strength-${result.level}`;
            }

            // Update requirements list
            this.updateRequirementsList(result.requirements);

            // Add visual feedback
            this.addVisualFeedback(result);
        }

        updateRequirementsList(requirements) {
            if (!this.requirementsList) return;
            
            // Update each requirement by matching data attributes
            requirements.forEach(requirement => {
                const item = this.requirementsList.querySelector(`[data-requirement="${requirement.id}"]`);
                if (item) {
                    const icon = item.querySelector('i');
                    
                    if (requirement.met) {
                        item.classList.add('met');
                        if (icon) icon.className = 'fa fa-check text-success';
                    } else {
                        item.classList.remove('met');
                        if (icon) icon.className = 'fa fa-times text-danger';
                    }
                }
            });
        }

        updateFormValidation(result) {
            const input = this.passwordInput;
            
            if (result.valid && input.value.length > 0) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else if (input.value.length > 0) {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-valid', 'is-invalid');
            }
        }

        addVisualFeedback(result) {
            // Add subtle animation to progress bar
            this.progressBar.style.transform = 'scaleX(0)';
            setTimeout(() => {
                this.progressBar.style.transform = 'scaleX(1)';
                this.progressBar.style.transition = 'transform 0.3s ease, width 0.3s ease';
            }, 50);

            // Haptic feedback on mobile devices
            if (navigator.vibrate && result.score > 0) {
                const intensity = Math.floor(result.score / 25);
                navigator.vibrate(intensity * 10);
            }
        }
    }

    // Initialize password strength validation
    function initPasswordStrength() {
        const passwordInput = document.getElementById('password');
        
        if (!passwordInput) {
            console.warn('Password input not found');
            return;
        }

        // Get validation rules from global variable
        const rules = window.signupValidationRules?.password || {};
        
        // Create validator and UI controller
        const validator = new PasswordStrengthValidator(rules);
        const ui = new PasswordStrengthUI(passwordInput, validator);

        console.log('Password strength validation initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPasswordStrength);
    } else {
        initPasswordStrength();
    }

    // Export for testing purposes
    window.PasswordStrengthValidator = PasswordStrengthValidator;
    window.PasswordStrengthUI = PasswordStrengthUI;

})();