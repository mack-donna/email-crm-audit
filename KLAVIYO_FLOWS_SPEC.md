# Klaviyo Prospect-to-Purchase Flow Specifications

## Overview
Strategic email/SMS automation flows designed to convert browsers into buyers and buyers into advocates, while feeding qualified prospects into the outreach automation system.

## Flow 1: Browse Abandon + Dynamic Social Proof

### Trigger Configuration
- **Event**: `Viewed Product` 
- **Condition**: No `Added to Cart` event within session
- **Delay**: 2 hours after last product view
- **Frequency Cap**: Max 2 browse abandon emails per week

### Segmentation Rules
- Exclude recent purchasers (30 days)
- Exclude active cart abandoners
- Priority score based on:
  - Number of products viewed
  - Time spent on site
  - Previous purchase history

### Email Sequence
**Email 1** (2 hours post-browse)
- Subject: "Still thinking about the {product_name}?"
- Dynamic product block with exact model viewed
- **Social Proof Element**: Rotating testimonial from `product.metafields.testimonials`
- Recent purchase activity ("12 others viewing now")
- CTA: "Complete Your Look"

**Email 2** (24 hours, if no action)
- Subject: "{first_name}, customers love this about the {product_name}"
- Feature comparison table
- **Social Proof Element**: Star rating + review count
- Customer quote highlighting specific benefit
- CTA: "Read More Reviews"

**Email 3** (72 hours, if no action)
- Subject: "Last chance to save on your favorites"
- 10% discount code (expires in 48 hours)
- Multiple product carousel (viewed items)
- **Social Proof Element**: "Best Seller" or "Staff Pick" badges
- CTA: "Claim Your Discount"

### Data Export to Outreach System
- Non-converters after 7 days → Export to CSV
- Fields: email, products_viewed, engagement_score, last_browse_date
- Tag: "browse_abandon_qualified"

---

## Flow 2: Cart Abandon + Creator Video

### Trigger Configuration
- **Event**: `Started Checkout`
- **Condition**: No `Placed Order` within 30 minutes
- **Channel Split**: Email (immediate) + SMS (if opted in)

### Segmentation Rules
- VIP customers get expedited sequence
- International vs domestic shipping messaging
- Price-based messaging (over/under $150)

### Multi-Channel Sequence

**SMS 1** (30 minutes post-abandon)
```
Hey {first_name}! You left something special in your cart 🛒

Watch this quick video about your {product_name}: 
{heygen_video_url}

Complete your order with FREE ENGRAVING: {engraving_code}
Expires in 2 hours!
```

**Email 1** (1 hour post-abandon)
- Subject: "{first_name}, we saved your cart"
- Cart contents with images
- **Video Element**: Embedded 15-second HeyGen video
  - Addresses top 2 concerns: warranty + fit
  - Personalized with product name
- Limited-time engraving offer
- CTA: "Complete Purchase"

**Email 2** (24 hours, if no action)
- Subject: "Your exclusive engraving code expires soon"
- Urgency messaging (code expires in 24 hours)
- Customer service chat widget
- Shipping & return policy highlights
- CTA: "Secure Your Items"

**SMS 2** (48 hours, if no action)
```
Last reminder: Your cart expires tonight!
{cart_value} worth of items
Free shipping included ✓
Reply HELP for assistance
```

### Data Export to Outreach System
- High-intent non-converters (opened all emails, clicked)
- Fields: email, cart_value, products_in_cart, abandon_count
- Tag: "high_intent_abandon"

---

## Flow 3: Post-Purchase + Referral Loop

### Trigger Configuration
- **Event**: `Fulfilled Order`
- **Timing**: Triggered when tracking shows "Out for Delivery"

### Customer Journey Mapping

**Pre-Delivery SMS** (Day of delivery)
```
{first_name}, your order arrives today! 📦

Share your unboxing for 20% off the matching display box:
{unboxing_upload_link}

Can't wait to see your setup!
```

**Email 1** (Day 1 post-delivery)
- Subject: "How's your new {product_name}?"
- Unboxing video request
- Incentive: 20% off matching display box
- Easy upload link (no account required)
- Setup tips and care instructions

**Email 2** (Day 7 post-delivery)
- Subject: "Ready to complete your collection?"
- Complementary product recommendations
- Customer's potential unboxing featured
- Referral program introduction
- CTA: "Shop Matching Accessories"

**Email 3** (Day 14 post-delivery)
- Subject: "You've earned VIP status"
- Review request (if no review yet)
- Referral code for friends (tracked discount)
- Loyalty points balance
- CTA: "Share Your Experience"

### Referral Mechanics
- Unique referral code per customer
- Two-sided incentive:
  - Referrer: $10 credit per successful referral
  - Referee: 15% off first purchase
- Automated tracking and reward distribution

### Data Export to Outreach System
- Customers who made 1 purchase but no repeat in 60 days
- Fields: email, purchase_value, product_category, review_status
- Tag: "reactivation_candidate"

---

## Technical Implementation

### Required Klaviyo Setup
1. **Custom Properties**
   - `heygen_video_url` (product-specific)
   - `engraving_code` (dynamic generation)
   - `testimonial_rotation` (A/B test variants)

2. **Webhooks**
   - Order fulfillment → Trigger video creation
   - Review submission → Update customer profile
   - Referral conversion → Credit distribution

3. **Integrations**
   - Shopify: Product metafields, inventory
   - HeyGen: Automated video generation
   - Twilio: SMS delivery
   - Outreach System: CSV export API

### Performance Metrics

#### Browse Abandon Flow
- Target: 5-8% conversion rate
- Email open rate: >40%
- Click rate: >8%

#### Cart Abandon Flow
- Target: 15-20% recovery rate
- SMS engagement: >25%
- Video watch rate: >60%

#### Post-Purchase Flow
- Target: 30% repeat purchase rate
- Referral activation: >15%
- Review submission: >25%

### A/B Testing Plan

1. **Subject Lines**
   - Urgency vs Benefit
   - Personalization vs Product focus
   - Emoji vs Plain text

2. **Send Times**
   - Immediate vs Delayed
   - Time of day optimization
   - Day of week testing

3. **Content Variations**
   - Video vs Static images
   - Long vs Short copy
   - Single vs Multiple CTAs

---

## Integration with Outreach Automation System

### Data Flow
```
Klaviyo → Weekly CSV Export → Contact Processor → Email Generator → Outreach Campaign
```

### Qualification Criteria
- Engaged but didn't convert (opened 2+ emails)
- High browse/cart value (>$200)
- Multiple site visits
- Email engagement without purchase

### Tagging Strategy
- `browse_abandon_qualified`: For targeted win-back
- `high_intent_abandon`: For personal outreach
- `reactivation_candidate`: For re-engagement campaigns

### Success Metrics
- Klaviyo → Outreach conversion: >10%
- Outreach → Purchase conversion: >5%
- Overall ROI: >400%

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Klaviyo account setup
- [ ] Shopify integration
- [ ] Custom property configuration

### Week 2: Browse Abandon Flow
- [ ] Email templates
- [ ] Dynamic content blocks
- [ ] Testimonial rotation logic

### Week 3: Cart Abandon Flow
- [ ] HeyGen video creation
- [ ] SMS integration
- [ ] Engraving code system

### Week 4: Post-Purchase Flow
- [ ] Unboxing upload portal
- [ ] Referral tracking
- [ ] Review request automation

### Week 5: Integration & Testing
- [ ] CSV export automation
- [ ] Outreach system connection
- [ ] End-to-end testing

### Week 6: Launch & Optimize
- [ ] Soft launch (10% traffic)
- [ ] Monitor metrics
- [ ] Full rollout

---

## Budget Estimation

### Monthly Costs
- Klaviyo: $500-1000 (based on list size)
- HeyGen API: $200 (video generation)
- SMS credits: $300
- Total: ~$1000-1500/month

### Expected Returns
- Browse abandon: $5,000/month
- Cart recovery: $8,000/month
- Referral sales: $3,000/month
- Repeat purchases: $4,000/month
- **Total Revenue Impact: $20,000/month**

### ROI: 13-20x monthly investment