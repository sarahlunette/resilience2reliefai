'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface Project {
  id: string
  title: string
  description: string
  sector: string[]
  priority_score: number
  estimated_budget: {
    estimated_amount: number
  }
  timeline: {
    duration: string
  }
  target_beneficiaries: {
    estimated_count: number
  }
  required_resources: string[]
  potential_partners: string[]
  sdg_alignment: number[]
}

interface ProjectResponse {
  success: boolean
  message: string
  data: {
    total_projects: number
    projects: Project[]
    metadata: any
  }
  timestamp: string
  processing_time: number
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [sectors, setSectors] = useState<string[]>([])
  const [regions, setRegions] = useState<string[]>([])
  const [disasterTypes, setDisasterTypes] = useState<string[]>([])
  const [maxProjects, setMaxProjects] = useState(5)
  const [budgetRange, setBudgetRange] = useState('')
  const [priority, setPriority] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const sectorOptions = [
    'infrastructure', 'health', 'education', 'agriculture', 
    'water', 'energy', 'housing', 'environment', 'economic', 'governance'
  ]

  const regionOptions = [
    'vanuatu', 'samoa', 'fiji', 'tonga', 'solomon_islands', 
    'png', 'marshall_islands', 'palau', 'kiribati', 'tuvalu'
  ]

  const disasterOptions = [
    'cyclone', 'earthquake', 'tsunami', 'flood', 
    'drought', 'wildfire', 'volcano'
  ]

  const toggleSelection = (item: string, list: string[], setList: (items: string[]) => void) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item))
    } else {
      setList([...list, item])
    }
  }

  const generateProjects = async () => {
    if (!query.trim() || query.length < 10) {
      setError('Please enter a query of at least 10 characters')
      return
    }

    setIsLoading(true)
    setError('')

    // Mock API call - replace with actual API endpoint
    try {
      // Simulated delay
      await new Promise(resolve => setTimeout(resolve, 3000))

      // Mock response data
      const mockResponse: ProjectResponse = {
        success: true,
        message: `Generated ${maxProjects} project proposals`,
        data: {
          total_projects: maxProjects,
          projects: Array.from({ length: maxProjects }, (_, i) => ({
            id: `project_${i + 1}`,
            title: `Disaster Recovery Project ${i + 1}`,
            description: `This is a comprehensive disaster recovery project addressing ${query}. The project focuses on sustainable reconstruction and community resilience building with innovative approaches to ${sectors.join(', ') || 'multiple sectors'}.`,
            sector: sectors.length > 0 ? sectors.slice(0, 2) : ['infrastructure'],
            priority_score: Math.floor(Math.random() * 5) + 6,
            estimated_budget: {
              estimated_amount: Math.floor(Math.random() * 20000000) + 5000000
            },
            timeline: {
              duration: `${Math.floor(Math.random() * 24) + 12} months`
            },
            target_beneficiaries: {
              estimated_count: Math.floor(Math.random() * 50000) + 5000
            },
            required_resources: [
              'Construction materials',
              'Technical expertise',
              'Community engagement',
              'Equipment and machinery'
            ],
            potential_partners: [
              'World Bank',
              'UNDP',
              'Local Government',
              'International NGOs'
            ],
            sdg_alignment: [3, 6, 9, 11, 13]
          })),
          metadata: {
            query,
            filters: { sectors, regions, disasterTypes, budgetRange, priority }
          }
        },
        timestamp: new Date().toISOString(),
        processing_time: 3.2
      }

      setProjects(mockResponse.data.projects)
    } catch (err) {
      setError('Failed to generate projects. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`
    }
    return `$${amount.toLocaleString()}`
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Resilience2Relief AI
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          AI-powered disaster recovery project generation system for Pacific Island nations. 
          Generate comprehensive recovery plans based on real disaster data and best practices.
        </p>
      </div>

      {/* Input Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Generate Disaster Recovery Projects</CardTitle>
          <CardDescription>
            Enter your requirements and we'll generate tailored recovery project proposals
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Main Query */}
          <div className="space-y-2">
            <Label htmlFor="query">Project Description *</Label>
            <Textarea
              id="query"
              placeholder="Describe the disaster recovery needs, e.g., 'Generate housing reconstruction projects for communities affected by Cyclone Pam in Vanuatu'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              className="min-h-[80px]"
            />
          </div>

          {/* Filters Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Sectors */}
            <div className="space-y-2">
              <Label>Sectors (Optional)</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[100px]">
                {sectorOptions.map((sector) => (
                  <Badge
                    key={sector}
                    variant={sectors.includes(sector) ? "default" : "outline"}
                    className="cursor-pointer capitalize"
                    onClick={() => toggleSelection(sector, sectors, setSectors)}
                  >
                    {sector}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Regions */}
            <div className="space-y-2">
              <Label>Target Regions (Optional)</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[100px]">
                {regionOptions.map((region) => (
                  <Badge
                    key={region}
                    variant={regions.includes(region) ? "default" : "outline"}
                    className="cursor-pointer capitalize"
                    onClick={() => toggleSelection(region, regions, setRegions)}
                  >
                    {region.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Disaster Types */}
            <div className="space-y-2">
              <Label>Disaster Types (Optional)</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[100px]">
                {disasterOptions.map((disaster) => (
                  <Badge
                    key={disaster}
                    variant={disasterTypes.includes(disaster) ? "default" : "outline"}
                    className="cursor-pointer capitalize"
                    onClick={() => toggleSelection(disaster, disasterTypes, setDisasterTypes)}
                  >
                    {disaster}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Additional Options */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="maxProjects">Number of Projects</Label>
              <Select value={maxProjects.toString()} onValueChange={(v) => setMaxProjects(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                    <SelectItem key={num} value={num.toString()}>{num}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="budgetRange">Budget Range (Optional)</Label>
              <Select value={budgetRange} onValueChange={setBudgetRange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select budget range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any budget</SelectItem>
                  <SelectItem value="1M-10M">$1M - $10M</SelectItem>
                  <SelectItem value="10M-50M">$10M - $50M</SelectItem>
                  <SelectItem value="50M-100M">$50M - $100M</SelectItem>
                  <SelectItem value="100M+">$100M+</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority Level (Optional)</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any priority</SelectItem>
                  <SelectItem value="high">High Priority</SelectItem>
                  <SelectItem value="medium">Medium Priority</SelectItem>
                  <SelectItem value="low">Low Priority</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Generate Button */}
          <Button 
            onClick={generateProjects}
            disabled={isLoading}
            className="w-full md:w-auto"
            size="lg"
          >
            {isLoading ? 'Generating Projects...' : 'Generate Recovery Projects'}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {projects.length > 0 && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Generated Projects ({projects.length})</h2>
            <Button variant="outline" size="sm">
              Export Results
            </Button>
          </div>

          <div className="grid gap-6">
            {projects.map((project) => (
              <Card key={project.id} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-xl">{project.title}</CardTitle>
                      <div className="flex items-center gap-4 mt-2">
                        <Badge variant="secondary">
                          Priority: {project.priority_score}/10
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {formatCurrency(project.estimated_budget.estimated_amount)}
                        </span>
                        <span className="text-sm text-gray-600">
                          {project.timeline.duration}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600 mb-1">Beneficiaries</div>
                      <div className="font-semibold">
                        {project.target_beneficiaries.estimated_count.toLocaleString()} people
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-gray-700">{project.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2">Sectors</h4>
                        <div className="flex flex-wrap gap-1">
                          {project.sector.map(s => (
                            <Badge key={s} variant="outline" className="capitalize text-xs">
                              {s}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-2">SDG Alignment</h4>
                        <div className="flex flex-wrap gap-1">
                          {project.sdg_alignment.map(sdg => (
                            <Badge key={sdg} variant="outline" className="text-xs">
                              SDG {sdg}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-2">Key Resources</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {project.required_resources.slice(0, 3).map((resource, i) => (
                            <li key={i}>• {resource}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-2">Potential Partners</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {project.potential_partners.slice(0, 3).map((partner, i) => (
                            <li key={i}>• {partner}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">View Details</Button>
                      <Button variant="outline" size="sm">Download PDF</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-16 text-center text-gray-500 text-sm">
        <p>Resilience2Relief AI - Powered by disaster recovery best practices and AI</p>
        <p>Supporting Pacific Island nations in building back better after disasters</p>
      </div>
    </div>
  )
}