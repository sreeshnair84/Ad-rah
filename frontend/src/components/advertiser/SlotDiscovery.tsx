'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Search,
  MapPin,
  Filter,
  Eye,
  Clock,
  DollarSign,
  Users,
  Star,
  Calendar,
  Monitor,
  Zap,
  TrendingUp,
  Heart,
  Info,
  ChevronDown,
  ChevronUp,
  Grid,
  List,
  Map,
  Bookmark,
  Share2,
  PlayCircle
} from 'lucide-react';

interface AdSlot {
  id: string;
  name: string;
  location: {
    id: string;
    name: string;
    address: string;
    city: string;
    state: string;
    coordinates: { lat: number; lng: number };
    venueType: string;
    footTraffic: string;
  };
  device: {
    screenSize: string;
    resolution: string;
    type: string;
  };
  pricing: {
    basePrice: number;
    peakMultiplier: number;
    weekendMultiplier: number;
    estimatedCPM: number;
  };
  availability: {
    totalSlots: number;
    availableSlots: number;
    nextAvailable: Date;
  };
  audience: {
    demographics: {
      ageGroups: string[];
      incomeLevel: string;
      interests: string[];
    };
    dailyViews: number;
    peakHours: string[];
  };
  performance: {
    rating: number;
    totalCampaigns: number;
    averageCTR: number;
    engagementScore: number;
  };
  restrictions: {
    contentTypes: string[];
    categories: string[];
    rating: string;
  };
  tags: string[];
  isFeatured: boolean;
  isBookmarked: boolean;
}

interface FilterState {
  search: string;
  location: {
    city: string;
    state: string;
    radius: number;
  };
  venue: string[];
  priceRange: number[];
  footTraffic: string[];
  demographics: {
    ageGroups: string[];
    incomeLevel: string[];
  };
  availability: {
    startDate: string;
    endDate: string;
    timeSlots: string[];
  };
  deviceType: string[];
  screenSize: string[];
  performance: {
    minRating: number;
    minCTR: number;
  };
}

export default function SlotDiscovery() {
  const [slots, setSlots] = useState<AdSlot[]>([]);
  const [filteredSlots, setFilteredSlots] = useState<AdSlot[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<AdSlot | null>(null);
  const [bookmarkedSlots, setBookmarkedSlots] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    location: {
      city: '',
      state: '',
      radius: 50
    },
    venue: [],
    priceRange: [0, 100],
    footTraffic: [],
    demographics: {
      ageGroups: [],
      incomeLevel: []
    },
    availability: {
      startDate: '',
      endDate: '',
      timeSlots: []
    },
    deviceType: [],
    screenSize: [],
    performance: {
      minRating: 0,
      minCTR: 0
    }
  });

  // Mock data for development
  useEffect(() => {
    const mockSlots: AdSlot[] = [
      {
        id: '1',
        name: 'Main Entrance Display',
        location: {
          id: 'loc1',
          name: 'Downtown Shopping Mall',
          address: '123 Main St',
          city: 'Seattle',
          state: 'WA',
          coordinates: { lat: 47.6062, lng: -122.3321 },
          venueType: 'retail',
          footTraffic: 'high'
        },
        device: {
          screenSize: '55"',
          resolution: '4K',
          type: 'LED Display'
        },
        pricing: {
          basePrice: 25.00,
          peakMultiplier: 1.5,
          weekendMultiplier: 1.2,
          estimatedCPM: 8.50
        },
        availability: {
          totalSlots: 48,
          availableSlots: 23,
          nextAvailable: new Date(Date.now() + 2 * 60 * 60 * 1000)
        },
        audience: {
          demographics: {
            ageGroups: ['25-34', '35-44'],
            incomeLevel: 'middle-high',
            interests: ['shopping', 'fashion', 'technology']
          },
          dailyViews: 15000,
          peakHours: ['11:00-13:00', '17:00-19:00']
        },
        performance: {
          rating: 4.5,
          totalCampaigns: 156,
          averageCTR: 2.1,
          engagementScore: 0.85
        },
        restrictions: {
          contentTypes: ['video', 'image', 'html5'],
          categories: ['retail', 'technology', 'lifestyle'],
          rating: 'PG'
        },
        tags: ['premium', 'high-traffic', 'retail'],
        isFeatured: true,
        isBookmarked: false
      },
      {
        id: '2',
        name: 'Food Court Central',
        location: {
          id: 'loc2',
          name: 'Metro Food Hall',
          address: '456 Broadway Ave',
          city: 'Seattle',
          state: 'WA',
          coordinates: { lat: 47.6124, lng: -122.3456 },
          venueType: 'food',
          footTraffic: 'high'
        },
        device: {
          screenSize: '65"',
          resolution: '4K',
          type: 'Interactive Display'
        },
        pricing: {
          basePrice: 20.00,
          peakMultiplier: 1.8,
          weekendMultiplier: 1.4,
          estimatedCPM: 12.00
        },
        availability: {
          totalSlots: 36,
          availableSlots: 18,
          nextAvailable: new Date(Date.now() + 4 * 60 * 60 * 1000)
        },
        audience: {
          demographics: {
            ageGroups: ['18-24', '25-34', '35-44'],
            incomeLevel: 'middle',
            interests: ['food', 'dining', 'social']
          },
          dailyViews: 12500,
          peakHours: ['12:00-14:00', '18:00-20:00']
        },
        performance: {
          rating: 4.2,
          totalCampaigns: 89,
          averageCTR: 3.2,
          engagementScore: 0.92
        },
        restrictions: {
          contentTypes: ['video', 'image', 'interactive'],
          categories: ['food', 'beverage', 'lifestyle'],
          rating: 'PG'
        },
        tags: ['interactive', 'food-audience', 'social'],
        isFeatured: false,
        isBookmarked: true
      },
      {
        id: '3',
        name: 'Gym Entry Monitor',
        location: {
          id: 'loc3',
          name: 'FitLife Gymnasium',
          address: '789 Health St',
          city: 'Bellevue',
          state: 'WA',
          coordinates: { lat: 47.5951, lng: -122.1426 },
          venueType: 'fitness',
          footTraffic: 'medium'
        },
        device: {
          screenSize: '43"',
          resolution: 'FHD',
          type: 'LED Display'
        },
        pricing: {
          basePrice: 15.00,
          peakMultiplier: 1.3,
          weekendMultiplier: 1.1,
          estimatedCPM: 6.80
        },
        availability: {
          totalSlots: 32,
          availableSlots: 28,
          nextAvailable: new Date(Date.now() + 1 * 60 * 60 * 1000)
        },
        audience: {
          demographics: {
            ageGroups: ['25-34', '35-44', '45-54'],
            incomeLevel: 'middle-high',
            interests: ['fitness', 'health', 'sports', 'wellness']
          },
          dailyViews: 5200,
          peakHours: ['06:00-08:00', '17:00-20:00']
        },
        performance: {
          rating: 4.0,
          totalCampaigns: 45,
          averageCTR: 1.8,
          engagementScore: 0.78
        },
        restrictions: {
          contentTypes: ['video', 'image'],
          categories: ['fitness', 'health', 'sports', 'nutrition'],
          rating: 'PG'
        },
        tags: ['fitness', 'health-focused', 'morning-peak'],
        isFeatured: false,
        isBookmarked: false
      }
    ];

    setSlots(mockSlots);
    setFilteredSlots(mockSlots);
  }, []);

  // Filter slots based on current filter state
  useEffect(() => {
    let filtered = [...slots];

    // Text search
    if (filters.search) {
      filtered = filtered.filter(slot => 
        slot.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        slot.location.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        slot.location.city.toLowerCase().includes(filters.search.toLowerCase()) ||
        slot.tags.some(tag => tag.toLowerCase().includes(filters.search.toLowerCase()))
      );
    }

    // Location filters
    if (filters.location.city) {
      filtered = filtered.filter(slot => 
        slot.location.city.toLowerCase().includes(filters.location.city.toLowerCase())
      );
    }

    // Venue type filter
    if (filters.venue.length > 0) {
      filtered = filtered.filter(slot => 
        filters.venue.includes(slot.location.venueType)
      );
    }

    // Price range filter
    filtered = filtered.filter(slot => 
      slot.pricing.basePrice >= filters.priceRange[0] &&
      slot.pricing.basePrice <= filters.priceRange[1]
    );

    // Foot traffic filter
    if (filters.footTraffic.length > 0) {
      filtered = filtered.filter(slot => 
        filters.footTraffic.includes(slot.location.footTraffic)
      );
    }

    // Performance filters
    filtered = filtered.filter(slot => 
      slot.performance.rating >= filters.performance.minRating &&
      slot.performance.averageCTR >= filters.performance.minCTR
    );

    setFilteredSlots(filtered);
  }, [filters, slots]);

  const handleBookmark = (slotId: string) => {
    setBookmarkedSlots(prev => 
      prev.includes(slotId) 
        ? prev.filter(id => id !== slotId)
        : [...prev, slotId]
    );
  };

  const handleSlotSelect = (slot: AdSlot) => {
    setSelectedSlot(slot);
  };

  const renderSlotCard = (slot: AdSlot) => (
    <Card key={slot.id} className="cursor-pointer hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center">
              {slot.name}
              {slot.isFeatured && (
                <Badge variant="secondary" className="ml-2 bg-yellow-100 text-yellow-800">
                  <Star className="h-3 w-3 mr-1" />
                  Featured
                </Badge>
              )}
            </CardTitle>
            <p className="text-sm text-gray-600 mt-1">
              <MapPin className="h-3 w-3 inline mr-1" />
              {slot.location.name}, {slot.location.city}
            </p>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBookmark(slot.id)}
            >
              <Heart className={`h-4 w-4 ${bookmarkedSlots.includes(slot.id) ? 'fill-red-500 text-red-500' : ''}`} />
            </Button>
            <Button variant="ghost" size="sm">
              <Share2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Device & Audience Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-medium">Device</p>
            <p className="text-gray-600">{slot.device.screenSize} {slot.device.type}</p>
            <p className="text-gray-600">{slot.device.resolution}</p>
          </div>
          <div>
            <p className="font-medium">Daily Views</p>
            <p className="text-gray-600">{slot.audience.dailyViews.toLocaleString()}</p>
            <div className="flex items-center">
              <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 mr-1" />
              <span>{slot.performance.rating}</span>
            </div>
          </div>
        </div>

        {/* Pricing */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm font-medium">Base Price</p>
              <p className="text-lg font-bold text-green-600">${slot.pricing.basePrice}/slot</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Est. CPM</p>
              <p className="text-sm font-semibold">${slot.pricing.estimatedCPM}</p>
            </div>
          </div>
        </div>

        {/* Availability */}
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-green-500" />
            <span className="text-sm">{slot.availability.availableSlots} slots available</span>
          </div>
          <Badge variant={slot.availability.availableSlots > 10 ? 'default' : 'destructive'}>
            {slot.availability.availableSlots > 10 ? 'Available' : 'Limited'}
          </Badge>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {slot.tags.map(tag => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-2 pt-2">
          <Button className="flex-1" onClick={() => handleSlotSelect(slot)}>
            <Eye className="h-4 w-4 mr-2" />
            View Details
          </Button>
          <Button variant="outline" className="flex-1">
            <Calendar className="h-4 w-4 mr-2" />
            Book Now
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderSlotList = (slot: AdSlot) => (
    <Card key={slot.id} className="mb-4">
      <CardContent className="p-4">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <div>
                <h3 className="font-semibold text-lg">{slot.name}</h3>
                <p className="text-sm text-gray-600">
                  {slot.location.name}, {slot.location.city}
                </p>
              </div>
              {slot.isFeatured && (
                <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                  Featured
                </Badge>
              )}
            </div>
            
            <div className="grid grid-cols-4 gap-4 mt-3 text-sm">
              <div>
                <p className="font-medium">Price</p>
                <p className="text-green-600 font-semibold">${slot.pricing.basePrice}/slot</p>
              </div>
              <div>
                <p className="font-medium">Daily Views</p>
                <p>{slot.audience.dailyViews.toLocaleString()}</p>
              </div>
              <div>
                <p className="font-medium">Available</p>
                <p>{slot.availability.availableSlots} slots</p>
              </div>
              <div>
                <p className="font-medium">Rating</p>
                <div className="flex items-center">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 mr-1" />
                  <span>{slot.performance.rating}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBookmark(slot.id)}
            >
              <Heart className={`h-4 w-4 ${bookmarkedSlots.includes(slot.id) ? 'fill-red-500 text-red-500' : ''}`} />
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleSlotSelect(slot)}>
              View Details
            </Button>
            <Button size="sm">
              Book Now
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Discover Ad Slots</h2>
          <p className="text-gray-600">Find the perfect advertising opportunities for your campaigns</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
            <Filter className="h-4 w-4 mr-2" />
            Filters
            {showFilters ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
          </Button>
          <div className="flex rounded-lg border">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'map' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('map')}
            >
              <Map className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search by location, venue type, or keywords..."
          className="pl-10"
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
        />
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle>Filters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Location Filters */}
              <div className="space-y-3">
                <Label>Location</Label>
                <Input
                  placeholder="City"
                  value={filters.location.city}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    location: { ...prev.location, city: e.target.value }
                  }))}
                />
                <Select
                  value={filters.location.state}
                  onValueChange={(value) => setFilters(prev => ({
                    ...prev,
                    location: { ...prev.location, state: value }
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="State" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="WA">Washington</SelectItem>
                    <SelectItem value="CA">California</SelectItem>
                    <SelectItem value="NY">New York</SelectItem>
                    <SelectItem value="TX">Texas</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Venue Type */}
              <div className="space-y-3">
                <Label>Venue Type</Label>
                <div className="space-y-2">
                  {['retail', 'food', 'fitness', 'transportation', 'office'].map(venue => (
                    <div key={venue} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.venue.includes(venue)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFilters(prev => ({
                              ...prev,
                              venue: [...prev.venue, venue]
                            }));
                          } else {
                            setFilters(prev => ({
                              ...prev,
                              venue: prev.venue.filter(v => v !== venue)
                            }));
                          }
                        }}
                      />
                      <Label className="capitalize">{venue}</Label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div className="space-y-3">
                <Label>Price Range ($/slot)</Label>
                <div className="px-2">
                  <Slider
                    value={filters.priceRange}
                    onValueChange={(value) => setFilters(prev => ({
                      ...prev,
                      priceRange: value
                    }))}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-600 mt-1">
                    <span>${filters.priceRange[0]}</span>
                    <span>${filters.priceRange[1]}</span>
                  </div>
                </div>
              </div>

              {/* Foot Traffic */}
              <div className="space-y-3">
                <Label>Foot Traffic</Label>
                <div className="space-y-2">
                  {['low', 'medium', 'high'].map(traffic => (
                    <div key={traffic} className="flex items-center space-x-2">
                      <Checkbox
                        checked={filters.footTraffic.includes(traffic)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFilters(prev => ({
                              ...prev,
                              footTraffic: [...prev.footTraffic, traffic]
                            }));
                          } else {
                            setFilters(prev => ({
                              ...prev,
                              footTraffic: prev.footTraffic.filter(t => t !== traffic)
                            }));
                          }
                        }}
                      />
                      <Label className="capitalize">{traffic}</Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Clear Filters */}
            <div className="flex justify-end">
              <Button
                variant="outline"
                onClick={() => setFilters({
                  search: '',
                  location: { city: '', state: '', radius: 50 },
                  venue: [],
                  priceRange: [0, 100],
                  footTraffic: [],
                  demographics: { ageGroups: [], incomeLevel: [] },
                  availability: { startDate: '', endDate: '', timeSlots: [] },
                  deviceType: [],
                  screenSize: [],
                  performance: { minRating: 0, minCTR: 0 }
                })}
              >
                Clear All Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      <div className="flex justify-between items-center">
        <p className="text-gray-600">
          Showing {filteredSlots.length} of {slots.length} ad slots
        </p>
        <Select defaultValue="relevance">
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="relevance">Sort by Relevance</SelectItem>
            <SelectItem value="price-low">Price: Low to High</SelectItem>
            <SelectItem value="price-high">Price: High to Low</SelectItem>
            <SelectItem value="rating">Highest Rated</SelectItem>
            <SelectItem value="views">Most Views</SelectItem>
            <SelectItem value="availability">Most Available</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Results */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
        {viewMode === 'map' ? (
          <Card className="col-span-full h-96">
            <CardContent className="flex items-center justify-center h-full">
              <div className="text-center">
                <Map className="h-12 w-12 mx-auto text-gray-400" />
                <p className="text-gray-600 mt-2">Map view coming soon</p>
                <p className="text-sm text-gray-500">Interactive map with slot locations</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredSlots.map(slot => 
            viewMode === 'grid' ? renderSlotCard(slot) : renderSlotList(slot)
          )
        )}
      </div>

      {/* Load More */}
      {filteredSlots.length > 0 && (
        <div className="flex justify-center">
          <Button variant="outline" disabled={loading}>
            {loading ? 'Loading...' : 'Load More Results'}
          </Button>
        </div>
      )}

      {/* Empty State */}
      {filteredSlots.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Search className="h-12 w-12 mx-auto text-gray-400" />
            <h3 className="text-lg font-semibold mt-4">No slots found</h3>
            <p className="text-gray-600 mt-2">Try adjusting your filters or search terms</p>
            <Button className="mt-4" onClick={() => setFilters(prev => ({ ...prev, search: '' }))}>
              Clear Search
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}