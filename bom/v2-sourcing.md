# V2 Hardware Sourcing Snapshot

Snapshot date: 2026-05-10.

This is a purchasing-oriented snapshot for the V2/Reachy-Mini-like SloppyTron
body:

- 7 structural servos: 6 Stewart/head servos plus 1 base yaw servo.
- 4 extra expression servos: custom ears and wings, not in the Reachy reference.
- 4-mic array.
- Speaker and small amplifier.

Prices and stock move quickly. Re-check every cart before buying.

## Recommendation

Best balance for a first V2 order:

| Use | Buy | Why |
| --- | --- | --- |
| Stewart/head, 6 axes | 6x ROBOTIS Dynamixel XL330-M288-T | This is the reference part and the shell/CAD assumptions fit the 20 x 34 x 26 mm X330 envelope. |
| Base yaw | 1x ROBOTIS Dynamixel XC330-M288-T, unless you redesign the base | Reachy names a custom XC330-M288-PG. The standard XC330-M288-T is the closest public part: same size class, stronger, metal gears. |
| Ears/wings, 4 axes | 4x Feetech SCS0009 or MG90S-class micro servos | These are low-risk expressive axes. Save money here rather than in the Stewart platform. |
| Mic array | Seeed reSpeaker XMOS XVF3800 4-Mic Array, no case for shell fit | Closest public equivalent to Reachy's XVF3800-based 4-mic array. USB is easiest on Pi 5. |
| Speaker | Seeed Mono Enclosed Speaker 4R 5W or Adafruit 40 mm 4 ohm 5 W | Both are cheap. Choose based on the final speaker cavity/grille. |
| Amp | MAX98357A I2S mono amp for simple voice output | Digital input from Pi, no analog audio path needed. It drives about 3 W, enough for voice. |

Avoid replacing the 6 Stewart/head servos with large cheap serial bus servos
unless you are ready to redesign the platform geometry and kinematics. Feetech
STS3215-class servos are attractive on price but are roughly 45.2 x 24.7 x
35 mm and about 55 g, versus XL330 at 20 x 34 x 26 mm and 18 g.

## Reference Components

The Reachy Mini hardware page lists:

- Stewart platform: 6x Dynamixel XL330-M288-T.
- Antennas: 2x Dynamixel XL330-M077-T.
- Base: 1x custom Dynamixel XC330-M288-PG, described as an XC330-M288-T with
  plastic gear.
- Mic array board: 4 PDM MEMS digital mics, based on Seeed Studio's reSpeaker
  XMOS XVF3800.
- Camera: Raspberry Pi Camera Module 3 Wide.
- Speaker: 5 W at 4 ohm.
- Power input: 6.8 to 7.6 V on the official power board.

Source: https://huggingface.co/docs/reachy_mini/platforms/reachy_mini/hardware

## Servos

### Structural head/Stewart servos

Recommended part: Dynamixel XL330-M288-T.

Key specs:

- Size: 20 x 34 x 26 mm.
- Weight: 18 g.
- Input voltage: 3.7 to 6 V, 5 V recommended.
- Stall torque: 0.52 Nm.
- Stall current: about 1.47 to 1.5 A.
- TTL bus, Protocol 2.0, 4096-step absolute position feedback.

Sources checked:

| Source | Snapshot |
| --- | --- |
| ROBOTIS US | $27.49, but product page says backordered, expected ship date mid-June. https://www.robotis.us/dynamixel-xl330-m288-t/ |
| ROBOTIS China / Taobao | ROBOTIS' e-Manual points to an official China Taobao channel. A public Koch arm BOM snapshot lists XL330-M288-T at RMB 255. A Taobao coupon mirror also showed some current XL330-M288-T listings around RMB 238 to 255. Direct Taobao usually needs a China-friendly checkout or forwarding workflow. https://emanual.robotis.com/docs/en/reference/dxl-selection-guide/ and https://github.com/jess-moss/koch-v1-1 and https://tao.hooos.com/tag_dynamixel%20xl330.html |
| China authorized partner / BJRobot | BJRobot describes itself as a long-running ROBOTIS China authorized partner and points to JD and Taobao stores. Useful authenticity signal, but direct Taobao/JD checkout from Switzerland may need a proxy. https://www.cnblogs.com/bjrobot/p/19648081 |
| Korean domestic robotics shops | Several Korean shops list XL330-M288-T around KRW 26,400, often with domestic-only shipping and sometimes sold out/backorder. This is a strong sticker price if a Korea proxy can buy and consolidate. Examples: https://miraerobot.com/product/xl330-m288-t/734/ and https://www.robolife-shop.co.kr/product/xl330-m288-t/288/display/1/ and https://ctrobot.co.kr/category/%EB%A1%9C%EB%B3%B4%ED%8B%B0%EC%A6%88-%EB%8B%A4%EC%9D%B4%EB%82%98%EB%AF%B9%EC%85%80-x/130/ |
| Korea open marketplaces | Watch out for inflated reseller listings. Coupang and Auction results showed XL330-M288-T listings around KRW 116,000 to 177,500, far above normal Korean robotics-shop pricing. https://www.coupang.com/vp/products/9420089778 and https://www.auction.co.kr/n/search?keyword=%EB%A1%9C%EB%B3%B4%ED%8B%B0%EC%A6%88 |
| AliExpress-style marketplace listings | Mixed value. I found marketplace mirrors/listings around US $49.90 or higher for XL330-M288-T, which is not cheaper than official/euro/Korea sources once import costs are included. Prefer official ROBOTIS channels or known authorized partners over anonymous marketplace listings. |
| Robotis.ch / NAPOJENO | $23.90 including VAT, in stock. Despite the `.ch` domain, the site describes itself as serving the Czech market and its shipping page lists CZ/EU carriers, so verify Switzerland delivery at checkout or use an EU parcel address. https://www.robotis.ch/53-xl330-m288-t |
| Galaxus Switzerland | CHF 39.90, supplier stock shown, free Swiss shipping above CHF 50. https://www.galaxus.ch/en/s1/product/robotis-dynamixel-xl330-m288-t-robotics-module-20432360 |
| Funduino Germany/EU | EUR 39.78 incl. VAT, Italian page showed 1-3 business days. https://funduinoshop.com/it/robotica/robotis/motoren/dynamixel-xl330-m288-t |
| Generation Robots France/EU | EUR 40.20 incl. French VAT, delivery within 4 weeks. https://www.generationrobots.com/en/403817-dynamixel-xl330-m288-t-servo-motor.html |

Buying note:

- For Switzerland direct delivery, Galaxus/Digitec is the simplest no-surprise
  source even though it is not the cheapest sticker price.
- For the lowest sticker price near Switzerland, try Robotis.ch/NAPOJENO first,
  but confirm it will ship to Switzerland. Its own shipping page lists CZ/EU
  delivery, not Switzerland.
- China can be cheaper if bought through the official ROBOTIS China/Taobao
  channel and shipped in a consolidated order. It is probably not cheaper via
  random AliExpress resellers, where listed prices can exceed Swiss/EU retail.
- Korea may be the cheapest genuine-source route by sticker price. The domestic
  retail price around KRW 26,400 is low, but many stores are domestic-shipping
  only, stock can be unstable, and a proxy/forwarder fee is likely. Search
  Korean terms: `XL330-M288-T`, `로보티즈 XL330-M288-T`, `다이나믹셀 XL330-M288-T`.
- For EU parcel-address or cross-border pickup, Robotis.ch/NAPOJENO is likely
  cheaper than German/French robotics resellers, even after Swiss VAT, if the
  checkout and carrier cooperate.
- ROBOTIS US is cheaper on sticker price than Galaxus, but backorder, shipping,
  Swiss VAT, and customs clearance fees can erase most of the savings.

#### Korean domestic route

This looks like the best low-price route if buying several genuine DYNAMIXEL
servos at once.

Normal Korean robotics-store pricing is much lower than Swiss/EU retail:

- XL330-M288-T: KRW 26,400 at MiraeRobot and Robolife; CTRobot also lists the
  model at KRW 26,400. Robolife showed a sold-out button during this snapshot,
  so verify stock at checkout.
- XC330-M288-T: KRW 96,800 at MiraeRobot/Robotpia-style domestic listings;
  CTRobot also shows XC330-M288-T around KRW 96,800, but some category pages
  mark it sold out.
- Avoid inflated Korean open-marketplace listings. Coupang/Auction style
  listings can be several times the domestic robotics-shop price.

Useful links:

- MiraeRobot XL330-M288-T: https://miraerobot.com/product/xl330-m288-t/734/
- Robolife XL330-M288-T: https://www.robolife-shop.co.kr/product/xl330-m288-t/288/display/1/
- CTRobot DYNAMIXEL X category: https://ctrobot.co.kr/category/%EB%A1%9C%EB%B3%B4%ED%8B%B0%EC%A6%88-%EB%8B%A4%EC%9D%B4%EB%82%98%EB%AF%B9%EC%85%80-x/130/
- MiraeRobot XC330-M288-T: https://miraerobot.com/product/xc330-m288-t/731
- Robotpia/STEMMALL XC330-M288-T: https://robotpia.net/product/xc330-m288-t-%EB%8B%A4%EC%9D%B4%EB%82%98%EB%AF%B9%EC%85%80-%EC%97%91%EC%B6%94%EC%97%90%EC%9D%B4%ED%84%B0/8019/display/1/

Ordering workflow from Switzerland:

1. Try the Korean shop checkout first. Some Cafe24 product pages display
   "overseas shipping possible", but the product data still says domestic
   courier, so treat this as "ask/verify", not guaranteed international
   delivery.
2. If the shop accepts a foreign card but only ships domestically, use a Korea
   warehouse forwarder and place the order yourself.
3. If the shop will not accept foreign payment, use a proxy buy-for-me service.
   KoreaBuyandShip publishes a 5% buying-service fee for TransferWise/Korea bank
   transfer-style payment and 10% for PayPal. Their Switzerland shipping table
   shows about USD 28.82 for 0.5 kg and USD 33.21 for 1.0 kg; ask for a quote
   if you use forwarding/address service rather than proxy purchasing.

Proxy/forwarder reference:

- KoreaBuyandShip service fees: https://koreabuyandship.com/service-fee/
- KoreaBuyandShip to Switzerland rates: https://koreabuyandship.com/switzerland/

Rough landed-cost estimate, using KRW 1 = about CHF 0.000536 and USD 1 = about
CHF 0.78:

| Cart | Korean item subtotal | Rough landed in Switzerland | Comparison |
| --- | ---: | ---: | --- |
| 6x XL330-M288-T | KRW 158,400, about CHF 85 | CHF 135-155 | Galaxus for 6x is CHF 239.40 before any base yaw servo. |
| 6x XL330-M288-T + 1x XC330-M288-T | KRW 255,200, about CHF 137 | CHF 195-215 | Could land below buying only the 6 XL330s from Galaxus. |
| 11x XL330-M288-T | KRW 290,400, about CHF 156 | CHF 220-250 | Only makes sense if you also want DYNAMIXELs for ears/wings. |

The landed estimates include a small domestic shipping allowance, proxy fee
where needed, 0.5 to 1.0 kg international forwarding, Swiss VAT, and a Swiss
Post-style non-EU customs-clearance benchmark. Courier brokerage can differ, so
leave about CHF 10-20 slack.

Pre-buy checklist:

- Model string must be exactly `XL330-M288-T` for the six Stewart/head servos.
- Confirm `-T` TTL, not RS-485.
- Do not accidentally buy `XL330-M077-T` unless using it for ears/wings.
- Confirm each retail box includes the X3P 180 mm cable and screws.
- Confirm the store has real quantity stock before paying a proxy.
- Ask the proxy to keep the invoice clear and accurate; Swiss customs uses the
  item price plus delivery/service costs to calculate import VAT.

Origin note: DYNAMIXEL is a ROBOTIS product line. ROBOTIS is a Korean company
founded in 1999, with sales subsidiaries including China. Treat China sourcing
as an official/local distribution-channel opportunity, not proof that the part is
a generic Chinese-manufactured servo.

Switzerland import note: Swiss Post says postal imports are charged Swiss VAT
when the VAT due reaches CHF 5, roughly CHF 63 of value including shipping at
the 8.1% standard rate. Swiss Post also charges customs-clearance service fees
of CHF 13 + 3% goods value for EU-origin consignments and CHF 16 + 3% for other
countries. Different rules apply if you personally bring goods over the border:
the traveller VAT-free limit is CHF 150 per person per day, and if exceeded,
VAT applies to the full imported value.

### Base yaw servo

Reference part: custom Dynamixel XC330-M288-PG. I did not find that as a public
retail item. Reachy documents it as an XC330-M288-T with plastic gear.

Practical public substitute: Dynamixel XC330-M288-T.

Key specs from RobotShop:

- Size: 20 x 34 x 26 mm.
- Weight: 23 g.
- Stall torque: 0.92 Nm.
- Stall current: 0.8 A.
- Metal gears and bearing; same X330 size class as XL330.

Source checked:

- RobotShop: $103.39, in stock, 44 units. https://www.robotshop.com/products/robotis-dynamixel-xc330-m288-t-smart-servo-actuator

Cheaper substitute if redesigning the base: a Feetech STS3215 7.4 V serial bus
servo. It is much larger, much heavier, and not Dynamixel protocol compatible,
but can be useful for a custom rotating pedestal.

### Extra ears and wings

These four axes do not have to match the Reachy reference. They should be
guarded as expression affordances with conservative speed and travel limits.

Option A, clean bus integration: 4x Dynamixel XL330-M077-T.

- Same 20 x 34 x 26 mm X330 envelope.
- Lower torque, faster than M288.
- Good if you want one Dynamixel bus and feedback everywhere.
- ROBOTIS US: $27.49, backordered to mid-June.
- Generation Robots: EUR 40.20, 362 available.
- Sources: https://www.robotis.us/dynamixel-xl330-m077-t/ and
  https://www.generationrobots.com/en/403818-dynamixel-xl330-m077-t-servo-motor.html

Option B, good cheap smart-servo choice: 4x Feetech SCS0009.

- Size: 23.2 x 12 x 25.5 mm.
- Weight: 12.5 g.
- Torque: 2.3 kg.cm at 6 V.
- TTL serial bus, feedback, lower wiring bulk than hobby PWM.
- Not Dynamixel protocol compatible; run it on a separate Feetech bus/driver.
- Retail: Abra Electronics listed US $17.97 in stock; Alibaba listings showed
  much lower unit prices in small quantity ranges, but supplier reliability
  needs checking.
- Source: https://abra-electronics.com/electromechanical/motors/servo-motors-feetech/scs0009.html

Option C, cheapest and simplest: MG90S-class metal-gear micro servos.

- Typical 9 g hobby servo format.
- Common AliExpress price range is low single-digit dollars per servo.
- Needs PCA9685 or a microcontroller servo bridge.
- No position/current/temperature feedback, so use mechanical stops and very
  conservative limits.
- Good for ears/wings, not for the Stewart head.

### Larger low-cost smart servo alternative

Feetech/Waveshare/DFRobot STS3215/ST3215 is the tempting low-cost alternative:

- DFRobot: $17.90 for 7.4 V 19.5 kg.cm version.
- BABSCO: $24.99, 76 available.
- AliExpress price tracker snapshot: US $16.61 / EUR 14.62.
- Size: about 45.2 x 24.7 x 35 mm.
- Weight: about 55 g.

Sources:

- https://www.dfrobot.com/product-2961.html
- https://shop.babsco.com/feetech-sts3215-19-5kg-smart-servo-c001
- https://ms.pricearchive.org/aliexpress.com/item/1005008728506501

Fit verdict: useful for a custom base or a from-scratch larger shell, but not a
minimal-modification replacement for XL330s in the Reachy-derived Stewart
platform. It changes the mass, link geometry, bus protocol, and power rail.

## Mic Array

Recommended: Seeed reSpeaker XMOS XVF3800 4-Mic Array, no case.

- USB and I2S modes.
- 4-mic circular array.
- Far-field 360 deg pickup up to 5 m.
- On-board AEC, AGC, DoA, VAD, dereverberation, beamforming, and noise
  suppression.
- Seeed direct: in stock, about $50 to $55 depending listing/variant; Seeed
  page says DE warehouse ships to EU when available.

Source:

- https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-Mic-Array-p-6488.html

Other variants:

- With case: $56.99 in stock. Good for bench testing, less ideal inside the
  shell. https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-4-Mic-Array-With-Case-p-6490.html
- Flex XVF3800 Linear/Circular: $49.90 in stock. Better if the final shell wants
  split boards or a non-round mic layout.
  https://www.seeedstudio.com/reSpeaker-Flex-XVF3800-Linear-4-p-6738.html
- Older ReSpeaker 4-Mic Array for Raspberry Pi: $24.90 but shown out of stock
  and discontinued. It is also a Pi HAT/I2S path, not as plug-and-play as USB.
  https://www.seeedstudio.com/ReSpeaker-4-Mic-Array-for-Raspberry-Pi.html

AliExpress note: I found Seeed XVF3800 listings through price trackers, but the
snapshot prices were higher than Seeed direct. One tracker showed US $79.17 for
a ReSpeaker XVF3800/XVF3000 series listing. Seeed direct currently looks better.

## Speaker And Amp

Reference target: 5 W at 4 ohm.

Speaker options:

| Part | Snapshot | Fit note |
| --- | --- | --- |
| Seeed Mono Enclosed Speaker 4R 5W | $2.00, in stock. https://www.seeedstudio.com/Mono-Enclosed-Speaker-4R-5W-p-5931.html | OpenELAB lists 50 x 45 x 22 mm. Good value, but slightly thicker than the current 58 x 18 mm CAD reservation. |
| Adafruit 40 mm 4 ohm 5 W speaker | $4.95, in stock. https://www.adafruit.com/product/3968 | Round 40 mm face, 20 mm height. Easier round grille, still needs about 2 mm more depth than the current reservation. |
| Generic AliExpress 4 ohm 5 W round speaker | Usually cheapest | Buy only after final grille/cavity dimensions are known. Verify actual diameter, depth, and mounting tabs. |

Amp options:

- MAX98357A I2S mono class-D amp: simplest Pi 5 path, about 3 W into 4 ohm at
  5 V. Good enough for speech, no analog DAC required.
- PAM8403 modules: very cheap 5 V analog stereo amps, often under $2, but Pi 5
  needs an analog output path or USB DAC.
- USB speaker: easiest software path, worst shell fit.

## Control And Power Items To Add To Cart

For Dynamixel axes:

- U2D2 USB communication converter. ROBOTIS US: $36.92, backordered to mid-June.
  U2D2 does not power the servos.
  https://www.robotis.us/u2d2/
- U2D2 Power Hub Board or equivalent power injection board.
  Generation Robots page showed 41 in stock.
  https://www.generationrobots.com/fr/403359-u2d2-power-hub-board.html
- Extra X3P JST Dynamixel cables in mixed lengths. Each XL330 includes one
  180 mm cable, but the Stewart platform and service loops will need spares.

Power guidance:

- Do not power servos from the Pi.
- Use a dedicated motor rail with shared ground to logic.
- For 7 XL/XC330-class structural axes, budget peak current around 10 A on the
  5 V servo rail before applying software current limiting.
- If all 11 axes are XL330-class, peak stall math is over 16 A. In practice the
  controller should never command that, but the rail, fuse, and cutoff should be
  designed for fault cases.
- If any STS3215/ST3215 axes are used, they need a separate 6 to 7.4 V rail and
  their locked-rotor current is much higher.
- Keep a reachable physical motor cutoff in series with the motor rail.

## Order Path

Practical staged order:

1. Buy 6x XL330-M288-T from an EU source if you want to move quickly.
2. Buy 1x XC330-M288-T for base yaw, or defer base yaw until the base bearing
   and mount are finalized.
3. Buy 4x SCS0009 for ears/wings if you accept a second serial bus, or 4x
   XL330-M077-T if you want one Dynamixel bus.
4. Buy the Seeed XVF3800 no-case mic array.
5. Buy one Seeed speaker and one Adafruit speaker; they are cheap enough that
   fit-testing both is worth it.
6. Buy MAX98357A, U2D2, a power hub, cable spares, fuses, and a motor cutoff.

Do not buy the final high-current regulator until the servo mix is locked,
because XL330/XC330 and STS3215-style servos want different rails.
