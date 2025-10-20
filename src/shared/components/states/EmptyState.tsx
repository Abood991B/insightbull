import { ReactNode } from 'react';
import { Button } from '@/shared/components/ui/button';
import { Card } from '@/shared/components/ui/card';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  actionLink?: string;
  secondaryAction?: {
    label: string;
    link: string;
  };
}

/**
 * Generic Empty State Component
 * Used across the application for consistent empty state UI
 */
export function EmptyState({ 
  icon, 
  title, 
  description, 
  actionLabel, 
  actionLink,
  secondaryAction 
}: EmptyStateProps) {
  return (
    <Card className="max-w-2xl mx-auto mt-12">
      <div className="flex flex-col items-center justify-center py-12 px-6">
        {icon}
        <h2 className="text-2xl font-bold text-gray-900 mt-4 mb-2">
          {title}
        </h2>
        <p className="text-gray-600 text-center mb-6 max-w-md">
          {description}
        </p>
        <div className="flex gap-4">
          {actionLabel && actionLink && (
            <Button asChild size="lg">
              <Link to={actionLink}>{actionLabel}</Link>
            </Button>
          )}
          {secondaryAction && (
            <Button variant="outline" asChild size="lg">
              <Link to={secondaryAction.link}>
                {secondaryAction.label}
              </Link>
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
