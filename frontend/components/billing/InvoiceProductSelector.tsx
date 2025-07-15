import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { InfoIcon, AlertCircle, ShoppingCart } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  description: string;
  prices: Price[];
}

interface Price {
  id: string;
  unit_amount: number;
  currency: string;
  type: 'one_time' | 'recurring';
  recurring?: {
    interval: string;
    interval_count: number;
  };
}

interface SelectedItem {
  product_id: string;
  price_id: string;
  quantity: number;
  product_name?: string;
  unit_amount?: number;
  price_type?: string;
  auto_added?: boolean;
  reason?: string;
}

interface ValidationResult {
  valid: boolean;
  items: SelectedItem[];
  warnings: string[];
  errors: string[];
}

export default function InvoiceProductSelector({ leadId, onSubmit }: { leadId: number; onSubmit: (items: SelectedItem[]) => void }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedItems, setSelectedItems] = useState<Map<string, SelectedItem>>(new Map());
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [totals, setTotals] = useState({ oneTime: 0, recurring: 0 });

  // Charger les produits Stripe
  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/billing/stripe-products');
      const data = await response.json();
      // Filtrer les produits qui ne sont pas des abonnements
      const mainProducts = data.products.filter((p: Product) => 
        !p.name.toLowerCase().includes('abonnement') && 
        !p.name.toLowerCase().includes('maintenance')
      );
      setProducts(mainProducts);
    } catch (error) {
      console.error('Erreur chargement produits:', error);
    }
  };

  // Valider la sélection à chaque changement
  useEffect(() => {
    if (selectedItems.size > 0) {
      validateSelection();
    }
  }, [selectedItems]);

  const validateSelection = async () => {
    const items = Array.from(selectedItems.values());
    
    try {
      const response = await fetch('/api/billing/validate-invoice-items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items)
      });
      
      const result: ValidationResult = await response.json();
      setValidationResult(result);
      
      // Calculer les totaux
      let oneTime = 0;
      let recurring = 0;
      
      result.items.forEach(item => {
        const amount = (item.unit_amount || 0) / 100;
        if (item.price_type === 'one_time') {
          oneTime += amount * (item.quantity || 1);
        } else {
          recurring += amount * (item.quantity || 1);
        }
      });
      
      setTotals({ oneTime, recurring });
    } catch (error) {
      console.error('Erreur validation:', error);
    }
  };

  const handleProductToggle = (product: Product, price: Price) => {
    const newSelection = new Map(selectedItems);
    const key = product.id;
    
    if (newSelection.has(key)) {
      newSelection.delete(key);
    } else {
      newSelection.set(key, {
        product_id: product.id,
        price_id: price.id,
        quantity: 1,
        product_name: product.name,
        unit_amount: price.unit_amount,
        price_type: price.type
      });
    }
    
    setSelectedItems(newSelection);
  };

  const handleSubmit = async () => {
    if (!validationResult || !validationResult.valid) return;
    
    setLoading(true);
    try {
      // Utiliser les items validés (incluant les abonnements ajoutés automatiquement)
      await onSubmit(validationResult.items);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount / 100);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sélectionner les produits</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            {products.map(product => {
              const price = product.prices.find(p => p.type === 'one_time') || product.prices[0];
              if (!price) return null;
              
              const isSelected = selectedItems.has(product.id);
              
              return (
                <div
                  key={product.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleProductToggle(product, price)}
                >
                  <div className="flex items-start gap-4">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => {}}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <h4 className="font-semibold">{product.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{product.description}</p>
                      <div className="mt-2">
                        <Badge variant="secondary">
                          {formatPrice(price.unit_amount)}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {validationResult && validationResult.warnings.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              {validationResult.warnings.map((warning, idx) => (
                <div key={idx}>{warning}</div>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {validationResult && validationResult.items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              Récapitulatif de la commande
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {validationResult.items.map((item, idx) => (
                <div key={idx} className="flex justify-between items-start py-2 border-b last:border-0">
                  <div className="flex-1">
                    <div className="font-medium">{item.product_name}</div>
                    {item.auto_added && (
                      <div className="text-sm text-orange-600 mt-1 flex items-center gap-1">
                        <InfoIcon className="h-3 w-3" />
                        {item.reason}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      {formatPrice(item.unit_amount || 0)}
                    </div>
                    {item.price_type === 'recurring' && (
                      <div className="text-sm text-gray-500">/mois</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t space-y-2">
              {totals.oneTime > 0 && (
                <div className="flex justify-between font-semibold">
                  <span>Total unique :</span>
                  <span>{formatPrice(totals.oneTime * 100)}</span>
                </div>
              )}
              {totals.recurring > 0 && (
                <div className="flex justify-between font-semibold text-blue-600">
                  <span>Total mensuel :</span>
                  <span>{formatPrice(totals.recurring * 100)}/mois</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end gap-3">
        <Button
          variant="outline"
          onClick={() => setSelectedItems(new Map())}
          disabled={selectedItems.size === 0}
        >
          Réinitialiser
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={!validationResult || !validationResult.valid || loading}
        >
          {loading ? 'Création...' : 'Créer la facture'}
        </Button>
      </div>
    </div>
  );
}