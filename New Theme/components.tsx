// ============================================================================
// EFIR BUDGET APP - REACT COMPONENT EXAMPLES
// Example implementations using the theme
// ============================================================================

import React from 'react';
import { 
  colors, 
  typography, 
  borderRadius, 
  shadows, 
  transitions, 
  moduleTheme, 
  statusTheme, 
  kpiTheme,
  progressTheme,
  type ModuleType, 
  type StatusType, 
  type KpiIndicator,
  type ProgressType,
} from './theme.constants';

// ============================================================================
// KPI CARD COMPONENT
// ============================================================================

interface KpiCardProps {
  label: string;
  value: string;
  unit: string;
  change: string;
  indicator: KpiIndicator;
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({ 
  label, 
  value, 
  unit, 
  change, 
  indicator,
  className = '',
}) => {
  const theme = kpiTheme[indicator];
  
  return (
    <div className={`relative bg-paper border border-border-light rounded-xl p-3.5 ${className}`}>
      {/* Bottom indicator bar */}
      <div 
        className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full"
        style={{ backgroundColor: theme.barColor }}
      />
      
      <div className="text-xs text-text-tertiary font-medium mb-1">
        {label}
      </div>
      
      <div className="flex items-baseline gap-1.5">
        <span 
          className="font-display text-kpi-xl font-semibold"
          style={{ color: indicator === 'negative' ? colors.accent.terracotta.DEFAULT : colors.text.primary }}
        >
          {value}
        </span>
        <span className="text-sm text-text-tertiary font-medium">
          {unit}
        </span>
      </div>
      
      <div 
        className="flex items-center gap-1 mt-1 text-xs"
        style={{ color: theme.textColor }}
      >
        <span>{theme.icon}</span>
        <span>{change}</span>
      </div>
    </div>
  );
};

// ============================================================================
// MODULE CARD COMPONENT
// ============================================================================

interface ModuleMetric {
  label: string;
  value: string;
  change?: string;
  changeDirection?: 'up' | 'down';
}

interface ModuleCardProps {
  type: ModuleType;
  title: string;
  description: string;
  status: StatusType;
  progress: number;
  metrics: ModuleMetric[];
  updatedAt: string;
  onClick?: () => void;
  className?: string;
}

export const ModuleCard: React.FC<ModuleCardProps> = ({
  type,
  title,
  description,
  status,
  progress,
  metrics,
  updatedAt,
  onClick,
  className = '',
}) => {
  const module = moduleTheme[type];
  const statusStyle = statusTheme[status];
  
  const getProgressType = (): ProgressType => {
    if (progress === 100) return 'complete';
    if (progress < 50) return 'low';
    return 'progress';
  };
  
  const getBorderClass = () => {
    if (status === 'alert') return 'border-l-[3px] border-l-terracotta';
    if (status === 'warning') return 'border-l-[3px] border-l-gold';
    return 'border-l border-l-border-light';
  };

  return (
    <div
      onClick={onClick}
      className={`
        bg-paper border border-border-light rounded-lg p-2.5 cursor-pointer
        transition-all hover:border-border-medium hover:shadow-sm
        ${getBorderClass()}
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-1.5">
        <div className="flex items-center gap-1.5">
          <div 
            className="w-6 h-6 rounded-md flex items-center justify-center text-[11px]"
            style={{ backgroundColor: module.bg, color: module.color }}
          >
            {module.icon}
          </div>
          <div>
            <h3 className="font-display text-md font-semibold text-text-primary leading-tight">
              {title}
            </h3>
            <p className="text-[8px] text-text-tertiary leading-snug">
              {description}
            </p>
          </div>
        </div>
        
        <span 
          className="text-[7px] px-1.5 py-0.5 rounded-full font-semibold whitespace-nowrap"
          style={{ backgroundColor: statusStyle.bg, color: statusStyle.color }}
        >
          {statusStyle.icon} {statusStyle.label}
        </span>
      </div>
      
      {/* Progress */}
      <div className="my-1.5">
        <div className="flex justify-between text-[8px] text-text-tertiary mb-0.5">
          <span>Planning Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="h-[3px] bg-subtle rounded-sm overflow-hidden">
          <div 
            className="h-full rounded-sm transition-all duration-300"
            style={{ 
              width: `${progress}%`,
              backgroundColor: progressTheme[getProgressType()].color,
            }}
          />
        </div>
      </div>
      
      {/* Metrics */}
      <div className="flex gap-2 mt-1.5">
        {metrics.map((metric, index) => (
          <div key={index} className="flex-1">
            <div className="text-[7px] text-text-muted uppercase tracking-wide">
              {metric.label}
            </div>
            <div className="font-display text-base font-semibold text-text-primary flex items-baseline gap-0.5">
              {metric.value}
              {metric.change && (
                <span 
                  className="font-body text-[7px]"
                  style={{ 
                    color: metric.changeDirection === 'down' 
                      ? colors.accent.terracotta.DEFAULT 
                      : colors.accent.sage.DEFAULT 
                  }}
                >
                  {metric.change}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Footer */}
      <div className="flex justify-between items-center mt-1.5 pt-1.5 border-t border-border-light">
        <span className="text-[8px] text-text-muted">
          🕐 {updatedAt}
        </span>
        <a 
          href="#" 
          className="text-[9px] text-gold font-medium hover:text-text-primary transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          Open →
        </a>
      </div>
    </div>
  );
};

// ============================================================================
// BADGE COMPONENT
// ============================================================================

type BadgeVariant = 'success' | 'warning' | 'error' | 'neutral' | 'info';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant, children, className = '' }) => {
  const variantClasses: Record<BadgeVariant, string> = {
    success: 'bg-sage-100 text-sage',
    warning: 'bg-status-warning-bg text-status-warning',
    error: 'bg-terracotta-100 text-terracotta',
    neutral: 'bg-subtle text-text-muted',
    info: 'bg-slate-100 text-slate',
  };
  
  return (
    <span className={`
      inline-flex items-center gap-0.5 px-1.5 py-0.5
      text-[7px] font-semibold rounded-full whitespace-nowrap
      ${variantClasses[variant]}
      ${className}
    `}>
      {children}
    </span>
  );
};

// ============================================================================
// BUTTON COMPONENT
// ============================================================================

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'gold';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'secondary',
  size = 'md',
  leftIcon,
  rightIcon,
  children,
  className = '',
  ...props
}) => {
  const variantClasses: Record<ButtonVariant, string> = {
    primary: 'bg-text-primary text-paper border-text-primary hover:bg-[#2D2C29]',
    secondary: 'bg-paper text-text-secondary border-border-light hover:bg-subtle hover:border-border-medium',
    ghost: 'bg-transparent text-text-secondary border-transparent hover:bg-subtle hover:text-text-primary',
    gold: 'bg-gold text-white border-gold hover:bg-gold-600',
  };
  
  const sizeClasses: Record<ButtonSize, string> = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };
  
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-1.5
        font-medium rounded-md border cursor-pointer
        transition-all duration-200
        focus-visible:outline-none focus-visible:shadow-focus
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      {...props}
    >
      {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
    </button>
  );
};

// ============================================================================
// QUICK ACTION BUTTON COMPONENT
// ============================================================================

interface QuickActionProps {
  icon: string;
  label: string;
  onClick?: () => void;
  className?: string;
}

export const QuickAction: React.FC<QuickActionProps> = ({ 
  icon, 
  label, 
  onClick,
  className = '',
}) => {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center justify-center gap-1.5
        py-2.5 px-3 bg-paper border border-border-light rounded-lg
        text-sm font-medium text-text-secondary
        transition-all duration-200
        hover:bg-subtle hover:border-border-medium hover:text-text-primary
        focus-visible:outline-none focus-visible:shadow-focus
        ${className}
      `}
    >
      <span className="text-sm">{icon}</span>
      {label}
    </button>
  );
};

// ============================================================================
// PROGRESS BAR COMPONENT
// ============================================================================

interface ProgressBarProps {
  value: number;
  type?: ProgressType;
  showLabel?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  type = 'progress',
  showLabel = false,
  className = '',
}) => {
  return (
    <div className={className}>
      {showLabel && (
        <div className="flex justify-between text-[8px] text-text-tertiary mb-0.5">
          <span>Progress</span>
          <span>{value}%</span>
        </div>
      )}
      <div className="h-[3px] bg-subtle rounded-sm overflow-hidden">
        <div 
          className="h-full rounded-sm transition-all duration-300"
          style={{ 
            width: `${Math.min(100, Math.max(0, value))}%`,
            backgroundColor: progressTheme[type].color,
          }}
        />
      </div>
    </div>
  );
};

// ============================================================================
// ICON CONTAINER COMPONENT
// ============================================================================

type IconSize = 'sm' | 'md' | 'lg' | 'xl';
type IconColor = 'gold' | 'sage' | 'terracotta' | 'slate' | 'wine' | 'neutral';

interface IconContainerProps {
  icon: React.ReactNode;
  size?: IconSize;
  color?: IconColor;
  className?: string;
}

export const IconContainer: React.FC<IconContainerProps> = ({
  icon,
  size = 'md',
  color = 'neutral',
  className = '',
}) => {
  const sizeClasses: Record<IconSize, string> = {
    sm: 'w-6 h-6 text-[11px]',
    md: 'w-8 h-8 text-sm',
    lg: 'w-[38px] h-[38px] text-base',
    xl: 'w-12 h-12 text-xl',
  };
  
  const colorClasses: Record<IconColor, string> = {
    gold: 'bg-gold-100 text-gold',
    sage: 'bg-sage-100 text-sage',
    terracotta: 'bg-terracotta-100 text-terracotta',
    slate: 'bg-slate-100 text-slate',
    wine: 'bg-wine-100 text-wine',
    neutral: 'bg-subtle text-text-tertiary',
  };
  
  return (
    <div className={`
      flex items-center justify-center rounded-lg
      ${sizeClasses[size]}
      ${colorClasses[color]}
      ${className}
    `}>
      {icon}
    </div>
  );
};

// ============================================================================
// CARD COMPONENT
// ============================================================================

type CardAccent = 'none' | 'gold' | 'sage' | 'terracotta' | 'slate' | 'wine';
type CardPadding = 'compact' | 'default' | 'spacious';

interface CardProps {
  children: React.ReactNode;
  accent?: CardAccent;
  padding?: CardPadding;
  hoverable?: boolean;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  accent = 'none',
  padding = 'default',
  hoverable = false,
  className = '',
  onClick,
}) => {
  const accentClasses: Record<CardAccent, string> = {
    none: '',
    gold: 'border-l-[3px] border-l-gold',
    sage: 'border-l-[3px] border-l-sage',
    terracotta: 'border-l-[3px] border-l-terracotta',
    slate: 'border-l-[3px] border-l-slate',
    wine: 'border-l-[3px] border-l-wine',
  };
  
  const paddingClasses: Record<CardPadding, string> = {
    compact: 'p-2.5',
    default: 'p-4',
    spacious: 'p-5',
  };
  
  return (
    <div
      onClick={onClick}
      className={`
        bg-paper border border-border-light rounded-xl
        transition-all duration-200
        ${hoverable ? 'cursor-pointer hover:border-border-medium hover:shadow-sm' : ''}
        ${accentClasses[accent]}
        ${paddingClasses[padding]}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

// ============================================================================
// INPUT COMPONENT
// ============================================================================

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  leftIcon,
  rightElement,
  className = '',
  ...props
}) => {
  return (
    <div className={`
      flex items-center gap-2
      px-3 py-1.5 bg-paper border border-border-light rounded-md
      transition-all duration-200
      focus-within:border-gold focus-within:shadow-focus
      ${className}
    `}>
      {leftIcon && <span className="text-text-muted flex-shrink-0">{leftIcon}</span>}
      <input
        className="
          flex-1 min-w-0 bg-transparent
          text-sm text-text-primary
          placeholder:text-text-muted
          focus:outline-none
        "
        {...props}
      />
      {rightElement && <span className="flex-shrink-0">{rightElement}</span>}
    </div>
  );
};

// ============================================================================
// KEYBOARD SHORTCUT COMPONENT
// ============================================================================

interface KbdProps {
  children: React.ReactNode;
  className?: string;
}

export const Kbd: React.FC<KbdProps> = ({ children, className = '' }) => {
  return (
    <kbd className={`
      inline-flex items-center justify-center
      px-1 py-0.5 bg-subtle rounded-sm
      text-[9px] text-text-tertiary font-body
      ${className}
    `}>
      {children}
    </kbd>
  );
};
