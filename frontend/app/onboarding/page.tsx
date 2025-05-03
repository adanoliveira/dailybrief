"use client"

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  getReferenceData, 
  Topic, 
  Region, 
  Language, 
  Publication 
} from '@/lib/feeds-service';
import { saveUserPreferences } from '@/lib/accounts-service';
import axios from 'axios';
import { getSession } from 'next-auth/react';

export default function OnboardingPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  // State for all the reference data
  const [topics, setTopics] = useState<Topic[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  
  // State for user selections
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedPublications, setSelectedPublications] = useState<string[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [step, setStep] = useState<'topics' | 'regions' | 'languages' | 'publications' | 'saving'>('topics');
  const [progress, setProgress] = useState(25);
  const [saving, setSaving] = useState(false);
  const [topicsInteracted, setTopicsInteracted] = useState(false);
  
  // Fetch reference data on component mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        console.log('Fetching reference data...');
        const data = await getReferenceData();
        
        // Sort data for better user experience
        const sortedTopics = [...data.topics].sort((a, b) => a.name.localeCompare(b.name));
        const sortedRegions = [...data.regions].sort((a, b) => a.name.localeCompare(b.name));
        const sortedLanguages = [...data.languages].sort((a, b) => a.name.localeCompare(b.name));
        
        // Sort publications by authority (if available) or alphabetically
        const sortedPublications = [...data.publications].sort((a, b) => {
          if (a.authority && b.authority) {
            return b.authority - a.authority; // Higher authority first
          }
          return a.name.localeCompare(b.name);
        });
        
        setTopics(sortedTopics);
        setRegions(sortedRegions);
        setLanguages(sortedLanguages);
        setPublications(sortedPublications);
        
        // Select English by default if available
        const englishLanguage = data.languages.find(lang => lang.iso_code === 'en');
        if (englishLanguage) {
          setSelectedLanguages([englishLanguage.id]);
        }
        
        console.log('Loaded reference data:', {
          topics: sortedTopics.length,
          regions: sortedRegions.length,
          languages: sortedLanguages.length,
          publications: sortedPublications.length
        });
        
        setLoading(false);
      } catch (error) {
        console.error('Failed to load reference data:', error);
        let errorMessage = 'Failed to load reference data.';
        
        if (error instanceof Error) {
          errorMessage += ` Error: ${error.message}`;
        }
        
        if (axios.isAxiosError(error)) {
          errorMessage += `\n\nRequest to: ${error.config?.baseURL}${error.config?.url}`;
          errorMessage += `\nMethod: ${error.config?.method?.toUpperCase()}`;
          
          if (error.response) {
            errorMessage += `\nStatus: ${error.response.status}`;
            if (error.response.data) {
              errorMessage += `\nDetails: ${JSON.stringify(error.response.data)}`;
            }
          } else if (error.request) {
            errorMessage += '\nNo response received from server';
          }
          
          // Check for missing token
          const session = await getSession();
          if (!session?.user?.django_token) {
            errorMessage += '\n\nMissing authentication token - please try logging in again';
          }
        }
        
        setLoadingError(errorMessage);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Update progress based on current step
  useEffect(() => {
    switch(step) {
      case 'topics':
        setProgress(25);
        break;
      case 'regions':
        setProgress(50);
        break;
      case 'languages':
        setProgress(75);
        break;
      case 'publications':
      case 'saving':
        setProgress(100);
        break;
    }
  }, [step]);
  
  // Handle topic selection
  const handleTopicToggle = (topicId: string) => {
    if (!topicsInteracted) {
      setTopicsInteracted(true);
    }
    
    setSelectedTopics(prev => 
      prev.includes(topicId) 
        ? prev.filter(id => id !== topicId)
        : [...prev, topicId]
    );
  };
  
  // Handle region selection
  const handleRegionToggle = (regionId: string) => {
    setSelectedRegions(prev => 
      prev.includes(regionId) 
        ? prev.filter(id => id !== regionId)
        : [...prev, regionId]
    );
  };
  
  // Handle language selection
  const handleLanguageToggle = (languageId: string) => {
    setSelectedLanguages(prev => 
      prev.includes(languageId) 
        ? prev.filter(id => id !== languageId)
        : [...prev, languageId]
    );
  };
  
  // Handle publication selection
  const handlePublicationToggle = (publicationId: string) => {
    setSelectedPublications(prev => 
      prev.includes(publicationId) 
        ? prev.filter(id => id !== publicationId)
        : [...prev, publicationId]
    );
  };
  
  // Navigation between steps
  const nextStep = () => {
    if (step === 'topics' && selectedTopics.length === 0) {
      setTopicsInteracted(true);
      toast({
        title: "Please select at least one topic",
        description: "You need to select at least one topic to continue.",
        variant: "destructive"
      });
      return;
    }
    
    if (step === 'topics') setStep('regions');
    else if (step === 'regions') setStep('languages');
    else if (step === 'languages') setStep('publications');
    else if (step === 'publications') handleSubmit();
  };
  
  const prevStep = () => {
    if (step === 'regions') setStep('topics');
    else if (step === 'languages') setStep('regions');
    else if (step === 'publications') setStep('languages');
  };
  
  // Filter publications based on selected topics, regions, and languages
  const getFilteredPublications = () => {
    return publications.filter(pub => {
      // If no relationships are provided, skip filtering
      if (!pub.topics || !pub.regions || !pub.languages) {
        return true;
      }
      
      // Only consider filtering if user has made selections
      const topicFilter = selectedTopics.length > 0 ? 
        pub.topics.some(topic => selectedTopics.includes(topic.id)) : true;
        
      const regionFilter = selectedRegions.length > 0 ? 
        pub.regions.some(region => selectedRegions.includes(region.id)) : true;
        
      const languageFilter = selectedLanguages.length > 0 ? 
        pub.languages.some(lang => selectedLanguages.includes(lang.id)) : true;
        
      return topicFilter && regionFilter && languageFilter;
    });
  };
  
  // Get filtered publications
  const filteredPublications = getFilteredPublications();
  
  // Handle final submission
  const handleSubmit = async () => {
    if (selectedTopics.length === 0) {
      toast({
        title: "Please select at least one topic",
        description: "You need to select at least one topic to complete setup.",
        variant: "destructive"
      });
      return;
    }
    
    setStep('saving');
    setSaving(true);
    
    try {
      console.log('Saving user preferences...');
      const result = await saveUserPreferences({
        topics: selectedTopics,
        regions: selectedRegions,
        languages: selectedLanguages,
        publications: selectedPublications,
      });
      
      toast({
        title: "Setup complete!",
        description: "Your preferences have been saved. Redirecting to your feed...",
      });
      
      // Hard redirect to /home with a query parameter to bypass middleware check
      // This completely reloads the app with a fresh session
      setTimeout(() => {
        window.location.href = '/home?new_session=true';
      }, 1500);
      
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setSaving(false);
      setStep('publications'); // Go back to publications step
      
      let errorMessage = 'An error occurred while saving your preferences.';
      
      if (error instanceof Error) {
        errorMessage += ` Error: ${error.message}`;
      }
      
      if (axios.isAxiosError(error)) {
        errorMessage += `\n\nRequest to: ${error.config?.baseURL}${error.config?.url}`;
        errorMessage += `\nMethod: ${error.config?.method?.toUpperCase()}`;
        
        if (error.response) {
          errorMessage += `\nStatus: ${error.response.status}`;
          if (error.response.data) {
            errorMessage += `\nDetails: ${JSON.stringify(error.response.data)}`;
          }
        } else if (error.request) {
          errorMessage += '\nNo response received from server';
        }
        
        // Check for missing token
        const session = await getSession();
        if (!session?.user?.django_token) {
          errorMessage += '\n\nMissing authentication token - please try logging in again';
        }
      }
      
      toast({
        title: "Failed to save preferences",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };
  
  // Show loading state
  if (loading) {
    return (
      <div className="container max-w-4xl py-10">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-1/3 mb-2" />
            <Skeleton className="h-4 w-2/3" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
              {Array.from({ length: 9 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full rounded-md" />
              ))}
            </div>
          </CardContent>
          <CardFooter>
            <Skeleton className="h-10 w-24" />
          </CardFooter>
        </Card>
      </div>
    );
  }
  
  // Show error state
  if (loadingError) {
    return (
      <div className="container max-w-4xl py-10">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{loadingError}</AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => window.location.reload()}>
          Refresh Page
        </Button>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-10">
      <Card>
        <CardHeader>
          <CardTitle>Welcome to DailyBrief!</CardTitle>
          <CardDescription>
            Let&apos;s personalize your experience. This will help us tailor your news feed.
          </CardDescription>
          <Progress value={progress} className="mt-4" />
        </CardHeader>
        
        {step === 'topics' && (
          <>
        <CardContent>
              <h3 className="text-lg font-medium mb-4">Select topics you&apos;re interested in</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {topics.map((topic) => (
                  <div key={topic.id} className="flex items-start space-x-2">
                    <Checkbox
                      id={`topic-${topic.id}`}
                      checked={selectedTopics.includes(topic.id)}
                      onCheckedChange={() => handleTopicToggle(topic.id)}
                    />
                    <Label 
                      htmlFor={`topic-${topic.id}`}
                      className="cursor-pointer font-normal"
                    >
                      {topic.name}
                    </Label>
                  </div>
                ))}
              </div>
              {topicsInteracted && selectedTopics.length === 0 && (
                <p className="text-sm text-red-500 mt-4">Please select at least one topic</p>
              )}
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button onClick={nextStep} disabled={selectedTopics.length === 0}>
                Next Step
              </Button>
            </CardFooter>
          </>
        )}
        
        {step === 'regions' && (
          <>
            <CardContent>
              <h3 className="text-lg font-medium mb-4">Select regions you want news from</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {regions.map((region) => (
                  <div key={region.id} className="flex items-start space-x-2">
                    <Checkbox 
                      id={`region-${region.id}`}
                      checked={selectedRegions.includes(region.id)}
                      onCheckedChange={() => handleRegionToggle(region.id)}
                    />
                    <Label 
                      htmlFor={`region-${region.id}`}
                      className="cursor-pointer font-normal"
                    >
                      {region.name}
                    </Label>
                </div>
                ))}
                </div>
              <p className="text-sm text-muted-foreground mt-4">
                Optional: If none selected, we&apos;ll include news from all regions
              </p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
                Back
              </Button>
              <Button onClick={nextStep}>
                Next Step
              </Button>
            </CardFooter>
          </>
        )}
        
        {step === 'languages' && (
          <>
            <CardContent>
              <h3 className="text-lg font-medium mb-4">Select languages for your news</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {languages.map((language) => (
                  <div key={language.id} className="flex items-start space-x-2">
                    <Checkbox 
                      id={`language-${language.id}`}
                      checked={selectedLanguages.includes(language.id)}
                      onCheckedChange={() => handleLanguageToggle(language.id)}
                    />
                    <Label 
                      htmlFor={`language-${language.id}`}
                      className="cursor-pointer font-normal"
                    >
                      {language.name}
                    </Label>
                  </div>
                ))}
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                We've selected English by default. You can choose multiple languages.
              </p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
                Back
              </Button>
              <Button onClick={nextStep}>
                Next Step
              </Button>
            </CardFooter>
          </>
        )}
        
        {step === 'publications' && (
          <>
            <CardContent>
              <h3 className="text-lg font-medium mb-4">Select your favorite news sources</h3>
              
              <Tabs defaultValue="recommended" className="mb-4">
                <TabsList className="mb-4">
                  <TabsTrigger value="recommended">Recommended</TabsTrigger>
                  <TabsTrigger value="all">All Sources ({filteredPublications.length})</TabsTrigger>
                  <TabsTrigger value="selected" disabled={selectedPublications.length === 0}>
                    Selected ({selectedPublications.length})
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="recommended">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredPublications
                      .filter(pub => pub.authority && pub.authority >= 8.5)
                      .map((publication) => (
                        <div key={publication.id} className="border rounded-md p-3 relative">
                          <div className="flex items-start">
                            <Checkbox 
                              id={`pub-${publication.id}`}
                              checked={selectedPublications.includes(publication.id)}
                              onCheckedChange={() => handlePublicationToggle(publication.id)}
                              className="mt-1"
                            />
                            <div className="ml-2">
                              <Label 
                                htmlFor={`pub-${publication.id}`}
                                className="cursor-pointer font-medium block"
                              >
                                {publication.name}
                              </Label>
                              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                {publication.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </TabsContent>
                
                <TabsContent value="all">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredPublications.map((publication) => (
                      <div key={publication.id} className="border rounded-md p-3 relative">
                        <div className="flex items-start">
                          <Checkbox 
                            id={`pub-all-${publication.id}`}
                            checked={selectedPublications.includes(publication.id)}
                            onCheckedChange={() => handlePublicationToggle(publication.id)}
                            className="mt-1"
                          />
                          <div className="ml-2">
                            <Label 
                              htmlFor={`pub-all-${publication.id}`}
                              className="cursor-pointer font-medium block"
                            >
                              {publication.name}
                            </Label>
                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                              {publication.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
                
                <TabsContent value="selected">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {publications
                      .filter(pub => selectedPublications.includes(pub.id))
                      .map((publication) => (
                        <div key={publication.id} className="border rounded-md p-3 relative">
                          <div className="flex items-start">
                            <Checkbox 
                              id={`pub-selected-${publication.id}`}
                              checked={true}
                              onCheckedChange={() => handlePublicationToggle(publication.id)}
                              className="mt-1"
                            />
                            <div className="ml-2">
                              <Label 
                                htmlFor={`pub-selected-${publication.id}`}
                                className="cursor-pointer font-medium block"
                              >
                                {publication.name}
                              </Label>
                              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                {publication.description}
                              </p>
                </div>
              </div>
            </div>
                      ))}
                  </div>
                </TabsContent>
              </Tabs>
              
              <p className="text-sm text-muted-foreground mt-4">
                Optional: If none selected, we&apos;ll include news from all sources based on your topics
              </p>
        </CardContent>
        <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
            Back
          </Button>
              <Button onClick={handleSubmit}>
                Finish Setup
              </Button>
        </CardFooter>
          </>
        )}
        
        {step === 'saving' && (
          <CardContent className="py-10 flex flex-col items-center justify-center">
            <h2 className="text-xl font-semibold mb-2">Setting up your personalized feed</h2>
            <p className="text-muted-foreground mb-4">This will just take a moment...</p>
            <div className="w-full max-w-xs">
              <Progress value={100} className="mb-4" />
            </div>
            <p className="text-sm">
              Selected {selectedTopics.length} topics, {selectedRegions.length} regions, {selectedLanguages.length} languages, 
              and {selectedPublications.length} publications
            </p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
