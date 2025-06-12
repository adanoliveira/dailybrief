import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Sparkles, ChevronDown, Loader2, AlertCircle, RefreshCw, Zap, Clock, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { withFormattingSupport } from "@/components/rich-article-renderer";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SummaryBlockProps {
  summary?: {
    headline?: string;
    abstract?: string;
    facts?: string[];
    opinions?: string[];
    impact?: string[];
    keyPoints?: string[]; // backwards compat
  };
  loading?: boolean;
  error?: string | null;
  onGenerate?: () => void;
}

export function SummaryBlock({ summary, loading, error, onGenerate }: SummaryBlockProps) {
  const [open, setOpen] = useState(false);

  // Accessible labels for expand/collapse
  const toggleLabel = open ? "Show less" : "Show more";

  const abstractText = summary?.abstract || "";

  // Collapsed preview: first 200 chars or first sentence
  const getPreview = (text: string) => {
    if (!text) return "";
    const firstSentence = text.match(/^.*?[.!?](\s|$)/);
    if (firstSentence && firstSentence[0].length < 200) return firstSentence[0];
    return text.slice(0, 200) + (text.length > 200 ? "..." : "");
  };

  return (
    <Card className="bg-primary/5 border-primary/20 mb-4 overflow-hidden">
      <CardContent className="p-0">
        {/* Only show section label when we have content */}
        {(summary || loading) && (
          <div className="px-4 pt-4 md:px-6 md:pt-6">
            <div className="mb-3 md:mb-4">
              <span className={cn(
                "text-xs md:text-sm font-medium uppercase tracking-wider",
                "text-muted-foreground/70 font-sans"
              )}>
                At a Glance
              </span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="px-4 pb-4 md:px-6 md:pb-6 pt-0">
            <div className="text-center space-y-4">
              <div className="flex flex-col items-center space-y-3">
                <div className="relative">
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                    <Loader2 className="w-6 h-6 text-primary animate-spin" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-primary rounded-full flex items-center justify-center">
                    <Sparkles className="w-2.5 h-2.5 text-primary-foreground animate-pulse" />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg text-foreground">
                    Analyzing article content
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto leading-relaxed">
                    Our AI is reading through the article to extract key insights and main points.
                  </p>
                </div>
              </div>
              
              {/* Progress indicator */}
              <div className="flex justify-center">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-primary/30 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-primary/50 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-primary/70 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-4 md:p-6">
            <div className="text-center space-y-4">
              <div className="flex flex-col items-center space-y-3">
                <div className="relative">
                  <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-6 h-6 text-destructive" />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg text-foreground">
                    Unable to generate summary
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto leading-relaxed">
                    Something went wrong while analyzing the article. Please try again in a moment.
                  </p>
                </div>
              </div>

              {/* Retry Button */}
              <Button 
                onClick={onGenerate} 
                variant="outline" 
                size="default"
                className="w-full sm:w-auto px-6 py-2.5 font-medium"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        )}

        {/* No summary, show generate button */}
        {!summary && !loading && !error && (
          <div className="p-4 md:p-6">
            <div className="text-center space-y-4">
              <div className="flex flex-col items-center space-y-3">
                <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                  <Zap className="w-5 h-5 text-primary" />
                </div>
                
                <div className="space-y-1">
                  <h3 className="font-semibold text-base text-foreground">
                    AI Summary Available
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Get main points and key insights in 30 seconds
                  </p>
                </div>
              </div>
              
              <Button 
                onClick={onGenerate} 
                className="w-full sm:w-auto font-medium" 
                variant="default"
                size="default"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Summary
              </Button>
            </div>
          </div>
        )}

        {/* Summary Display */}
        {summary && !loading && !error && (
          <Collapsible open={open} onOpenChange={setOpen}>
            <CollapsibleTrigger asChild>
              <button
                className={cn(
                  "w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
                  "relative"
                )}
                aria-expanded={open}
                aria-label={open ? "Show less details" : "Show more details"}
              >
                <div className="px-4 pb-4 md:px-6 md:pb-6">
                  <div className="space-y-3">
                    {/* Headline */}
                    {summary.headline && (
                      <h3 className={withFormattingSupport(cn(
                        "font-black tracking-tight scroll-m-20 leading-tight font-sans text-foreground",
                        "text-xl md:text-2xl lg:text-3xl xl:text-4xl"
                      ))}>
                        {summary.headline}
                      </h3>
                    )}
                    {/* Abstract */}
                    <div className={withFormattingSupport(cn(
                      "text-base md:text-lg leading-relaxed font-serif text-foreground/90 article-content-font"
                    ))}>
                      {abstractText}
                    </div>
                  </div>
                </div>
              </button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-0">
              <div className="border-t border-border/10">
                <ScrollArea className="px-6 md:px-8 pb-6">
                  {/* Facts */}
                  {summary.facts && summary.facts.length > 0 && (
                    <div className="pt-3">
                      <h4 className={withFormattingSupport(cn(
                        "font-bold tracking-tight scroll-m-20 leading-tight font-sans text-foreground/90",
                        "text-base md:text-lg mb-2"
                      ))}>Main Points</h4>
                      <ul className={withFormattingSupport(cn(
                        "list-disc space-y-1.5 text-base md:text-lg text-foreground/90 article-content-font leading-snug ml-5"
                      ))}>
                        {summary.facts.map((fact, i) => (
                          <li key={i} className="pl-2">{cleanPrefix(fact)}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Opinions */}
                  {summary.opinions && summary.opinions.length > 0 && (
                    <div className="mt-5">
                      <h4 className={withFormattingSupport(cn(
                        "font-bold tracking-tight scroll-m-20 leading-tight font-sans text-foreground/90",
                        "text-base md:text-lg mb-2"
                      ))}>Key Perspectives</h4>
                      <ul className={withFormattingSupport(cn(
                        "list-disc space-y-1.5 text-base md:text-lg text-foreground/90 article-content-font leading-snug ml-5"
                      ))}>
                        {summary.opinions.map((op, i) => (
                          <li key={i} className="pl-2">{cleanPrefix(op)}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Impact */}
                  {summary.impact && summary.impact.length > 0 && (
                    <div className="mt-5">
                      <h4 className={withFormattingSupport(cn(
                        "font-bold tracking-tight scroll-m-20 leading-tight font-sans text-foreground/90",
                        "text-base md:text-lg mb-2"
                      ))}>Potential Impact</h4>
                      <ul className={withFormattingSupport(cn(
                        "list-disc space-y-1.5 text-base md:text-lg text-foreground/90 article-content-font leading-snug ml-5"
                      ))}>
                        {summary.impact.map((imp, i) => (
                          <li key={i} className="pl-2">{cleanPrefix(imp)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </ScrollArea>
              </div>

              {/* Fixed toggle button at bottom */}
              <div className="px-6 md:px-8 pt-0 pb-4 md:pb-6 bg-gradient-to-t from-background/80 to-transparent sticky bottom-0">
                <button
                  onClick={() => setOpen(false)}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 py-2",
                    "text-sm font-medium text-primary hover:text-primary/80 transition-colors",
                    "border border-border/40 rounded-md hover:bg-accent/50"
                  )}
                >
                  Show less details
                  <ChevronDown className="h-4 w-4 rotate-180" />
                </button>
              </div>
            </CollapsibleContent>

            {/* Show more button when collapsed */}
            {!open && (
              <div className="px-4 md:px-6 pt-0 pb-4 md:pb-6">
                <button
                  onClick={() => setOpen(true)}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 py-2",
                    "text-sm font-medium text-primary hover:text-primary/80 transition-colors",
                    "border border-border/40 rounded-md hover:bg-accent/50"
                  )}
                >
                  Read key details
                  <ChevronDown className="h-4 w-4" />
                </button>
              </div>
            )}
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}

// Helper to clean prefixed tags like [FACT] or ⚡
function cleanPrefix(text: string): string {
  return text.replace(/^\s*\[(FACT|STAT|IMPACT)\]\s*/i, "").replace(/^⚡\s*/, "").trim();
} 