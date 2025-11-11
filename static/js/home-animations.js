/**
 * Home Page Animations
 * DUT Hospital - Professional Medical Clinic System
 */

(function() {
    'use strict';

    /**
     * Counter Animation for Stats Section
     */
    function animateCounter(element, start, end, duration) {
        const range = end - start;
        const increment = end > start ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        let current = start;
        
        const timer = setInterval(() => {
            current += increment * Math.ceil(range / 100);
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = formatNumber(current);
        }, stepTime);
    }

    /**
     * Format number with comma separators
     */
    function formatNumber(num) {
        return Math.floor(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * Initialize counter animations when elements come into view
     */
    function initCounters() {
        const counters = document.querySelectorAll('.stat-number[data-count]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                    const target = entry.target;
                    const count = parseInt(target.getAttribute('data-count'));
                    target.classList.add('animated');
                    animateCounter(target, 0, count, 2000);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => observer.observe(counter));
    }

    /**
     * Smooth scroll for anchor links
     */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    const headerOffset = 80;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    /**
     * Add scroll animations to sections
     */
    function initScrollAnimations() {
        const animatedElements = document.querySelectorAll('.service-card, .testimonial-card, .feature-box');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '0';
                        entry.target.style.transform = 'translateY(30px)';
                        entry.target.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                        
                        requestAnimationFrame(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        });
                    }, index * 100);
                    
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(element => {
            observer.observe(element);
        });
    }

    /**
     * Parallax effect for hero section
     */
    function initParallax() {
        const heroSection = document.querySelector('.hero-section');
        if (!heroSection) return;

        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * 0.5;
            
            if (heroSection) {
                heroSection.style.transform = `translateY(${rate}px)`;
            }
        });
    }

    /**
     * Sticky header on scroll
     */
    function initStickyHeader() {
        const header = document.querySelector('header');
        if (!header) return;

        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;

            if (currentScroll > 100) {
                header.classList.add('scrolled');
                
                // Hide header on scroll down, show on scroll up
                if (currentScroll > lastScroll && currentScroll > 300) {
                    header.style.transform = 'translateY(-100%)';
                } else {
                    header.style.transform = 'translateY(0)';
                }
            } else {
                header.classList.remove('scrolled');
                header.style.transform = 'translateY(0)';
            }

            lastScroll = currentScroll;
        });
    }

    /**
     * Add hover effect to service cards
     */
    function initServiceCardEffects() {
        const serviceCards = document.querySelectorAll('.service-card');
        
        serviceCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.zIndex = '10';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.zIndex = '1';
            });
        });
    }

    /**
     * Testimonial slider (simple version)
     */
    function initTestimonialSlider() {
        const testimonials = document.querySelectorAll('.testimonial-card');
        if (testimonials.length === 0) return;

        let currentIndex = 0;

        // Auto rotate testimonials highlight every 5 seconds
        setInterval(() => {
            testimonials.forEach((card, index) => {
                if (index === currentIndex) {
                    card.style.transform = 'scale(1.05)';
                    card.style.boxShadow = '0 20px 50px rgba(0, 0, 0, 0.2)';
                } else {
                    card.style.transform = 'scale(1)';
                    card.style.boxShadow = '0 5px 25px rgba(0, 0, 0, 0.08)';
                }
            });
            
            currentIndex = (currentIndex + 1) % testimonials.length;
        }, 5000);
    }

    /**
     * Add animation to CTA buttons
     */
    function initCTAAnimations() {
        const ctaButtons = document.querySelectorAll('.hero-actions .btn, .cta-section .btn');
        
        ctaButtons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.05)';
                this.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
                this.style.boxShadow = '';
            });
        });
    }

    /**
     * Lazy load images
     */
    function initLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    /**
     * Add progress bar on page scroll
     */
    function initScrollProgressBar() {
        // Create progress bar element
        const progressBar = document.createElement('div');
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            z-index: 10000;
            transition: width 0.1s ease;
        `;
        document.body.appendChild(progressBar);

        window.addEventListener('scroll', () => {
            const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (window.pageYOffset / windowHeight) * 100;
            progressBar.style.width = scrolled + '%';
        });
    }

    /**
     * Initialize all animations
     */
    function init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Initialize all features
        initCounters();
        initSmoothScroll();
        initScrollAnimations();
        initStickyHeader();
        initServiceCardEffects();
        initTestimonialSlider();
        initCTAAnimations();
        initLazyLoading();
        initScrollProgressBar();
        
        // Parallax is heavy on mobile, only enable on desktop
        if (window.innerWidth > 992) {
            initParallax();
        }

        console.log('✅ Home page animations initialized');
    }

    // Auto-initialize
    init();

    // Expose methods for manual control if needed
    window.homeAnimations = {
        reinit: init
    };

})();

