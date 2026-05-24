import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';

class HomeBanner extends StatelessWidget {
  const HomeBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 160,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFE0F2F1), Color(0xFFF1F8F7)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(28),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned(
            left: -20,
            top: 10,
            child: Opacity(
              opacity: 0.2,
              child: Image.asset(
                "assets/decor/clouds/decor-cloud-mint-01.png",
                width: 140,
              ),
            ),
          ),
          Positioned(
            left: 160,
            top: 5,
            child: Opacity(
              opacity: 0.25,
              child: Image.asset(
                "assets/decor/clouds/decor-cloud-mint-01.png",
                width: 130,
              ),
            ),
          ),
          Positioned(
            left: 140,
            bottom: 5,
            child: Opacity(
              opacity: 0.2,
              child: Image.asset(
                "assets/decor/clouds/decor-cloud-mint-01.png",
                width: 110,
              ),
            ),
          ),
          Positioned(
            left: -10,
            top: -15,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset(
                "assets/decor/botanical/decor-leaf-sprig-03.png",
                width: 100,
              ),
            ),
          ),
          Positioned(
            left: 20,
            bottom: -5,
            child: Opacity(
              opacity: 0.4,
              child: Image.asset(
                "assets/decor/botanical/decor-leaf-sprig-02.png",
                width: 70,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(left: 24, top: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  "home.banner_title".tr(context: context),
                  style: GoogleFonts.outfit(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF00695C),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  "home.banner_subtitle".tr(context: context),
                  style: GoogleFonts.inter(
                    fontSize: 15,
                    color: const Color(0xFF4DB6AC),
                  ),
                ),
              ],
            ),
          ),
          Positioned(
            right: 0,
            top: 15,
            child: Opacity(
              opacity: 0.4,
              child: Image.asset(
                "assets/decor/clouds/decor-cloud-mint-01.png",
                width: 130,
              ),
            ),
          ),
          Positioned(
            right: -45,
            bottom: -35,
            child: Image.asset(
              "assets/mascot/mascot-owl-reading-book.png",
              height: 250,
              fit: BoxFit.contain,
            ),
          ),
          Positioned(
            right: 0,
            bottom: -15,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset(
                "assets/decor/botanical/decor-leaf-double-01.png",
                width: 90,
              ),
            ),
          ),
          Positioned(
            left: -5,
            bottom: -5,
            child: Opacity(
              opacity: 0.3,
              child: Image.asset(
                "assets/decor/botanical/decor-leaf-single-01.png",
                width: 60,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
