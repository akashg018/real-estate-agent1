from .base_agent import BaseAgent
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

logger = logging.getLogger(__name__)

class DealClosingAgent(BaseAgent):
    """
    Intelligent deal closing agent that manages the final stages of property purchase
    and updates database status
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def process_deal(self, property_id: int, deal_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process property deal closing with comprehensive workflow"""
        try:
            logger.info(f"Processing deal closure for property {property_id}")
            
            # Validate property exists and is available
            property_data = self.db_manager.get_property(property_id)
            if not property_data:
                return self._standardize_response(
                    "error",
                    f"Property {property_id} not found",
                    {}
                )
            
            if not property_data.get('is_available', True):
                return self._standardize_response(
                    "error",
                    "This property is no longer available for purchase",
                    {}
                )
            
            # Generate comprehensive closing plan
            closing_plan = self._generate_closing_plan(property_data, deal_details)
            
            # Calculate closing costs
            closing_costs = self._calculate_closing_costs(property_data, deal_details)
            
            # Generate timeline
            timeline = self._generate_closing_timeline()
            
            # Prepare documentation list
            documentation = self._prepare_documentation_list(property_data, deal_details)
            
            return self._standardize_response(
                "success",
                self._generate_closing_message(property_data, closing_plan),
                {
                    "property_id": property_id,
                    "property_info": {
                        "address": property_data['address'],
                        "price": property_data['price'],
                        "type": property_data['property_type']
                    },
                    "closing_plan": closing_plan,
                    "closing_costs": closing_costs,
                    "timeline": timeline,
                    "documentation": documentation,
                    "next_immediate_steps": self._get_immediate_steps(),
                    "team_contacts": self._get_team_contacts(),
                    "status": "initiated"
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing deal closure for property {property_id}: {e}")
            return self._standardize_response(
                "error",
                f"Failed to process deal closure: {str(e)}",
                {}
            )

    def finalize_deal(self, property_id: int) -> Dict[str, Any]:
        """Finalize the deal and update database"""
        try:
            logger.info(f"Finalizing deal for property {property_id}")
            
            # Update property availability in database
            success = self.db_manager.update_property_availability(property_id, False)
            
            if success:
                # Generate completion documentation
                completion_docs = self._generate_completion_documentation(property_id)
                
                return self._standardize_response(
                    "success",
                    "🎉 Congratulations! Your property purchase has been completed successfully!",
                    {
                        "property_id": property_id,
                        "completion_date": datetime.now().isoformat(),
                        "status": "completed",
                        "database_updated": True,
                        "completion_documentation": completion_docs,
                        "post_closing_steps": self._get_post_closing_steps(),
                        "celebration_message": "Welcome to your new home! 🏠✨"
                    }
                )
            else:
                return self._standardize_response(
                    "error",
                    "Deal completion successful, but database update failed",
                    {"property_id": property_id, "database_updated": False}
                )
                
        except Exception as e:
            logger.error(f"Error finalizing deal for property {property_id}: {e}")
            return self._standardize_response(
                "error",
                f"Failed to finalize deal: {str(e)}",
                {}
            )

    def _generate_closing_plan(self, property_data: Dict[str, Any], deal_details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive closing plan using AI"""
        try:
            property_price = property_data['price']
            property_type = property_data['property_type']
            address = property_data['address']
            city = property_data['city']
            state = property_data['state']
            
            closing_prompt = f"""
            Generate a detailed real estate closing plan for:
            
            Property: {property_type} at {address}, {city}, {state}
            Purchase Price: ${property_price:,.2f}
            Deal Details: {deal_details}
            
            Return JSON with comprehensive closing plan:
            {{
                "phases": [
                    {{
                        "name": "phase name",
                        "duration": "X days",
                        "tasks": ["task1", "task2"],
                        "responsible_parties": ["buyer", "seller", "agent", "lender"],
                        "deliverables": ["document1", "document2"]
                    }}
                ],
                "critical_milestones": [
                    {{
                        "milestone": "milestone name",
                        "deadline": "relative date",
                        "importance": "high|medium|low"
                    }}
                ],
                "potential_risks": [
                    {{
                        "risk": "risk description",
                        "mitigation": "mitigation strategy",
                        "probability": "high|medium|low"
                    }}
                ]
            }}
            """
            
            default_plan = self._get_default_closing_plan(property_data)
            ai_plan = self.generate_structured_response_sync(closing_prompt, default_plan)
            
            return ai_plan
            
        except Exception as e:
            logger.error(f"Error generating closing plan: {e}")
            return self._get_default_closing_plan(property_data)

    def _get_default_closing_plan(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get default closing plan structure"""
        return {
            "phases": [
                {
                    "name": "Contract Execution",
                    "duration": "1-2 days",
                    "tasks": ["Sign purchase agreement", "Submit earnest money", "Review terms"],
                    "responsible_parties": ["buyer", "seller", "agents"],
                    "deliverables": ["Signed contract", "Earnest money receipt"]
                },
                {
                    "name": "Due Diligence",
                    "duration": "7-14 days",
                    "tasks": ["Property inspection", "Appraisal", "Title search", "HOA review"],
                    "responsible_parties": ["buyer", "inspector", "appraiser", "title company"],
                    "deliverables": ["Inspection report", "Appraisal report", "Title commitment"]
                },
                {
                    "name": "Financing",
                    "duration": "14-21 days",
                    "tasks": ["Loan application", "Underwriting", "Final approval"],
                    "responsible_parties": ["buyer", "lender", "underwriter"],
                    "deliverables": ["Loan commitment", "Closing disclosure"]
                },
                {
                    "name": "Pre-Closing",
                    "duration": "3-5 days",
                    "tasks": ["Final walkthrough", "Wire transfer setup", "Closing preparation"],
                    "responsible_parties": ["buyer", "seller", "agents", "title company"],
                    "deliverables": ["Walkthrough checklist", "Wire instructions"]
                },
                {
                    "name": "Closing",
                    "duration": "1 day",
                    "tasks": ["Document signing", "Fund transfer", "Key handover"],
                    "responsible_parties": ["buyer", "seller", "title agent", "agents"],
                    "deliverables": ["Deed", "Keys", "Closing statement"]
                }
            ],
            "critical_milestones": [
                {"milestone": "Inspection completion", "deadline": "10 days", "importance": "high"},
                {"milestone": "Loan approval", "deadline": "21 days", "importance": "high"},
                {"milestone": "Final walkthrough", "deadline": "1 day before closing", "importance": "medium"}
            ],
            "potential_risks": [
                {"risk": "Inspection issues", "mitigation": "Negotiate repairs or credits", "probability": "medium"},
                {"risk": "Appraisal low", "mitigation": "Renegotiate price or bring cash", "probability": "low"},
                {"risk": "Financing delays", "mitigation": "Have backup lender ready", "probability": "medium"}
            ]
        }

    def _calculate_closing_costs(self, property_data: Dict[str, Any], deal_details: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate estimated closing costs"""
        try:
            purchase_price = property_data['price']
            state = property_data.get('state', 'CA')
            
            # State-specific tax rates (simplified)
            state_rates = {
                'CA': {'transfer_tax': 0.0011, 'recording_fee': 150},
                'NY': {'transfer_tax': 0.004, 'recording_fee': 200},
                'TX': {'transfer_tax': 0.0, 'recording_fee': 100},
                'FL': {'transfer_tax': 0.007, 'recording_fee': 125},
                'IL': {'transfer_tax': 0.001, 'recording_fee': 175}
            }
            
            rates = state_rates.get(state, state_rates['CA'])
            
            # Calculate individual costs
            costs = {
                "lender_fees": {
                    "origination_fee": round(purchase_price * 0.005, 2),
                    "appraisal_fee": random.randint(400, 600),
                    "credit_report": random.randint(25, 50),
                    "underwriting_fee": random.randint(400, 800)
                },
                "title_insurance": {
                    "owners_policy": round(purchase_price * 0.005, 2),
                    "lenders_policy": round(purchase_price * 0.0025, 2),
                    "title_search": random.randint(200, 400)
                },
                "government_fees": {
                    "transfer_tax": round(purchase_price * rates['transfer_tax'], 2),
                    "recording_fee": rates['recording_fee'],
                    "document_stamps": random.randint(50, 150)
                },
                "third_party_services": {
                    "inspection": random.randint(300, 600),
                    "survey": random.randint(400, 800),
                    "pest_inspection": random.randint(75, 150)
                },
                "prepaid_items": {
                    "homeowners_insurance": round(purchase_price * 0.003, 2),
                    "property_taxes": round(purchase_price * 0.012 / 12 * 2, 2),  # 2 months
                    "hoa_fees": random.randint(0, 500)
                },
                "escrow_reserves": {
                    "insurance_reserve": round(purchase_price * 0.003 / 12 * 2, 2),
                    "tax_reserve": round(purchase_price * 0.012 / 12 * 2, 2)
                }
            }
            
            # Calculate totals
            category_totals = {}
            grand_total = 0
            
            for category, items in costs.items():
                category_total = sum(items.values())
                category_totals[category] = category_total
                grand_total += category_total
            
            return {
                "detailed_costs": costs,
                "category_totals": category_totals,
                "estimated_total": round(grand_total, 2),
                "percentage_of_price": round((grand_total / purchase_price) * 100, 2),
                "cash_needed": round(grand_total + purchase_price * 0.2, 2),  # Assuming 20% down
                "disclaimer": "Costs are estimates and may vary based on specific lender and service providers"
            }
            
        except Exception as e:
            logger.error(f"Error calculating closing costs: {e}")
            return {"estimated_total": 0, "error": "Could not calculate costs"}

    def _generate_closing_timeline(self) -> Dict[str, Any]:
        """Generate detailed closing timeline"""
        today = datetime.now()
        
        timeline = {
            "contract_execution": {
                "start_date": today.strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                "status": "pending"
            },
            "due_diligence_period": {
                "start_date": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=14)).strftime('%Y-%m-%d'),
                "status": "upcoming"
            },
            "financing_approval": {
                "start_date": (today + timedelta(days=3)).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=24)).strftime('%Y-%m-%d'),
                "status": "upcoming"
            },
            "final_walkthrough": {
                "start_date": (today + timedelta(days=28)).strftime('%Y-%m-%d'),
                "end_date": (today + timedelta(days=29)).strftime('%Y-%m-%d'),
                "status": "scheduled"
            },
            "closing_day": {
                "target_date": (today + timedelta(days=30)).strftime('%Y-%m-%d'),
                "estimated_time": "2-3 hours",
                "status": "scheduled"
            }
        }
        
        return {
            "timeline": timeline,
            "total_duration": "30-35 days",
            "key_deadlines": [
                {"task": "Inspection", "deadline": (today + timedelta(days=10)).strftime('%Y-%m-%d')},
                {"task": "Loan approval", "deadline": (today + timedelta(days=21)).strftime('%Y-%m-%d')},
                {"task": "Final walkthrough", "deadline": (today + timedelta(days=29)).strftime('%Y-%m-%d')}
            ]
        }

    def _prepare_documentation_list(self, property_data: Dict[str, Any], deal_details: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive documentation checklist"""
        return {
            "buyer_documents": {
                "financial": [
                    "Pre-approval letter",
                    "Bank statements (2-3 months)",
                    "Pay stubs (recent)",
                    "Tax returns (2 years)",
                    "Employment verification letter"
                ],
                "personal": [
                    "Government-issued ID",
                    "Social Security card",
                    "Proof of homeowner's insurance",
                    "Cashier's check for closing costs"
                ]
            },
            "seller_documents": [
                "Property deed",
                "Property disclosures",
                "HOA documents (if applicable)",
                "Warranty information",
                "Utility bills and transfer forms"
            ],
            "transaction_documents": [
                "Purchase agreement",
                "Inspection reports",
                "Appraisal report",
                "Title commitment",
                "Loan documents",
                "Closing disclosure"
            ],
            "post_closing_documents": [
                "Recorded deed",
                "Title insurance policy",
                "Final closing statement",
                "Keys and garage door openers",
                "Warranty documents"
            ]
        }

    def _get_immediate_steps(self) -> List[Dict[str, Any]]:
        """Get immediate next steps for buyer"""
        return [
            {
                "step": "Sign purchase agreement",
                "timeline": "Within 24 hours",
                "priority": "high",
                "description": "Review and sign the purchase agreement with your real estate agent"
            },
            {
                "step": "Submit earnest money",
                "timeline": "Within 48 hours",
                "priority": "high",
                "description": "Transfer earnest money to escrow account as specified in contract"
            },
            {
                "step": "Schedule inspection",
                "timeline": "Within 3-5 days",
                "priority": "high",
                "description": "Book professional property inspection during contingency period"
            },
            {
                "step": "Finalize financing",
                "timeline": "Within 1 week",
                "priority": "medium",
                "description": "Submit final loan application documents to your lender"
            }
        ]

    def _get_team_contacts(self) -> Dict[str, Any]:
        """Get team contact information (simulated)"""
        return {
            "real_estate_agent": {
                "name": "Sarah Johnson",
                "phone": "(555) 123-4567",
                "email": "sarah.johnson@realestate.com",
                "role": "Buyer's Agent"
            },
            "lender": {
                "name": "Michael Chen",
                "phone": "(555) 234-5678",
                "email": "mchen@mortgage.com",
                "role": "Loan Officer"
            },
            "title_company": {
                "name": "Premier Title Services",
                "phone": "(555) 345-6789",
                "email": "info@premiertitle.com",
                "role": "Title & Escrow"
            },
            "inspector": {
                "name": "Expert Home Inspections",
                "phone": "(555) 456-7890",
                "email": "info@experthome.com",
                "role": "Property Inspector"
            }
        }

    def _generate_completion_documentation(self, property_id: int) -> Dict[str, Any]:
        """Generate completion documentation"""
        completion_date = datetime.now()
        
        return {
            "completion_certificate": {
                "property_id": property_id,
                "completion_date": completion_date.isoformat(),
                "status": "completed",
                "reference_number": f"TXN-{property_id}-{completion_date.strftime('%Y%m%d')}"
            },
            "next_deliverables": [
                "Recorded deed (7-10 business days)",
                "Title insurance policy (14 days)",
                "Property tax assessment update (30-60 days)"
            ],
            "digital_assets": [
                "Electronic copy of all signed documents",
                "Property photos and virtual tour access",
                "Warranty and manual documents",
                "Home maintenance schedule"
            ]
        }

    def _get_post_closing_steps(self) -> List[Dict[str, Any]]:
        """Get post-closing steps for new homeowner"""
        return [
            {
                "category": "immediate",
                "tasks": [
                    "Change locks and security codes",
                    "Set up utilities in your name",
                    "Update address with bank, employer, IRS",
                    "Purchase homeowner's insurance"
                ]
            },
            {
                "category": "first_week",
                "tasks": [
                    "Meet neighbors and get emergency contacts",
                    "Locate and test main water/gas shutoffs",
                    "Register with local waste management",
                    "Update voter registration"
                ]
            },
            {
                "category": "first_month",
                "tasks": [
                    "Schedule HVAC maintenance",
                    "Review and organize warranty documents",
                    "Plan any immediate repairs or improvements",
                    "Research local contractors and services"
                ]
            }
        ]

    def _generate_closing_message(self, property_data: Dict[str, Any], closing_plan: Dict[str, Any]) -> str:
        """Generate personalized closing message"""
        try:
            address = property_data['address']
            property_type = property_data['property_type']
            price = property_data['price']
            
            phases = len(closing_plan.get('phases', []))
            
            message = f"🎉 Excellent! Let's close on your {property_type} at {address}!\n\n"
            message += f"💰 Purchase Price: ${price:,.2f}\n"
            message += f"📋 Process: {phases} phases over 30-35 days\n\n"
            message += "Your dedicated closing team is ready to guide you through every step. "
            message += "We'll handle the complex paperwork while keeping you informed of all progress. "
            message += "Get ready to receive your keys! 🔑✨"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating closing message: {e}")
            return "Ready to close on your property! Let's get started with the process."
